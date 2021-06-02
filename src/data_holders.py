from dataclasses import dataclass
import pandas as pd
import numpy as np
import datetime

from src import travel_time, publish_mqtt

@dataclass
class Traces:
    """This dataclass holds a reference to the Traces DF in memory."""

    data: pd.DataFrame = pd.DataFrame()

    print("✅ Created empty dataframe for sensor data.")

    def update(self, data, cloud_t):

        # print("Message delay: " + str(cloud_t-data["cloud_send"]))

        device_id = data["device_id"]
        x = data["traces"][0]["x"]
        y = data["traces"][0]["y"]
        z = data["traces"][0]["z"]
        sr = 31.25

        if "cloud_t" in data:
            cloud_t = data["cloud_t"]

        if any([len(x) != len(y), len(x) != len(z), len(y) != len(z)]):
            sampnum = min([len(x), len(y), len(z)])
            x = x[0:sampnum]
            y = y[0:sampnum]
            z = z[0:sampnum]

        data = {
            "device_id": device_id,
            "x": x,
            "y": y,
            "z": z,
            "sr": sr,
            "cloud_t": cloud_t,
        }

        # create cloud_time vector and replicate device_id
        number_of_entires = len(data["x"])
        sr = data["sr"]
        data["device_id"] = [data["device_id"]] * number_of_entires
        data["cloud_t"] = list(cloud_t - np.arange(0, number_of_entires)[::-1] / sr)

        # create a df
        df_new = pd.DataFrame(data)

        # append to the data
        self.data = self.data.append(df_new, ignore_index=True)

    def drop(self, params):

        # get timestamp for the received trace
        dt = datetime.datetime.now(datetime.timezone.utc)
        utc_time = dt.replace(tzinfo=datetime.timezone.utc)
        cloud_t = utc_time.timestamp()

        # drop all data older than cloud_t - buffer
        try:
            self.data = self.data[
                (self.data["cloud_t"] + params["buffer_len"]) >= cloud_t
            ]
            # print(
            #     "▫️ Size of data in the buffer "
            #     + str(int(sys.getsizeof(self.data) / 1e5) / 10)
            #     + " mb"
            # )
        except:
            pass


@dataclass
class Detections:
    """This dataclass holds a reference to the Detections DF in memory."""

    print("✅ Created empty dataframe for detections.")

    data: pd.DataFrame = pd.DataFrame(
        columns=[
            "detection_id",
            "device_id",
            "cloud_t",
            "mag1",
            "mag2",
            "mag3",
            "mag4",
            "mag5",
            "mag6",
            "mag7",
            "mag8",
            "mag9",
            "event_id",
        ]
    )

    def update(self, data):
        self.data = self.data.append(data, ignore_index=True)

    def drop(self, event_id, params):

        # publish old detections to mqtt
        old_detections = self.data[self.data["event_id"] == event_id]

        for _, det in old_detections.iterrows():
            json_data = det.to_dict()

            publish_mqtt.run("detection", json_data, params)

        self.data = self.data[self.data["event_id"] != event_id]


@dataclass
class Devices:
    """This dataclass holds a reference to the Devices DF in memory."""

    print("✅ Created empty dataframe for devices.")

    data: pd.DataFrame = pd.DataFrame()


@dataclass
class Events:
    """This dataclass holds a reference to the Events DF in memory."""

    print("✅ Created empty dataframe for events.")

    data: pd.DataFrame = pd.DataFrame(
        columns=[
            "event_id",
            "cloud_t",
            "orig_time",
            "lat",
            "lon",
            "dep",
            "mag",
            "mconf2",
            "mconf16",
            "mconf84",
            "mconf98",
            "num_assoc",
        ]
    )

    def update(self, data):

        # create a df
        df_new = pd.DataFrame(data, index=[0])

        # append to the data
        self.data = self.data.append(df_new, ignore_index=True)

    def drop(self, event_id):

        self.data = self.data[self.data["event_id"] != event_id]
        # print("▫️ Number of events in the buffer " + str(len(self.data)))

    def publish_event(self, params, event_id):
        """Publishes event to mqtt"""

        event = self.data[self.data["event_id"] == event_id].iloc[-1]

        if event["num_assoc"] >= params["ndef_min"]:

            json_data = event.to_dict()
            publish_mqtt.run("event", json_data, params)


class TravelTimes:
    """This dataclass holds a reference to the TravelTimes in memory."""

    print("✅ Creating travel times instance.")

    def __init__(self, params):

        # save travel time params
        self.params = params

        # open or calculate new travel time tables
        tt = travel_time.get_travel_time(params)

        # load or calculate new travel time vector
        self.tt_vector = tt["tt_vector"]

        # create latitude and longitude grid
        self.grid_lat = tt["grid_lat"]
        self.grid_lon = tt["grid_lon"]

        # create empty dictionary for travel times
        self.tt_grid = tt["tt_grid"]
