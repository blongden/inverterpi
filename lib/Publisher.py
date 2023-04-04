class Publisher:
    def __init__(self, client, mqtt=None) -> None:
        self.client = client
        self.mqtt = mqtt # any object that implements an method of publish(topic, payload)

    def publish_state(self, state):
        publish_failure = False
        rc = 0

        if self.mqtt:
            for name in state.keys():
                if state[name] is None:
                    continue

                rc = self.mqtt.publish(f"{self.client}/{name}", state[name]).rc
                if rc != 0:
                    publish_failure = True
                    break
        
        return (publish_failure, rc)

