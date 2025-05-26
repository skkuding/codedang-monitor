import requests
import json
import datetime
import time
import os

# from message_card_template import message_card

# Prometheus 서버 주소
PROMETHEUS_URL = "http://prometheus:9090"

# MS Teams Incoming Webhook URL
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# Prometheus queries
QUERIES = {
    "api-client": 'count by (instance) (group(system_cpu_utilization{job="backend-client-metric"}))',
    "api-admin": 'count by (instance) (group(system_cpu_utilization{job="backend-admin-metric"}))',
    "iris": 'count by (instance) (group(cpu_usage_percent{job="iris-metric"}))',
}


def fetch_metrics(query):
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


def get_instance_counts():
    data = {}
    for key, query in QUERIES.items():
        result = fetch_metrics(query)
        if result and result["data"]["result"]:
            data[key] = int(result["data"]["result"][0]["value"][1])
    return data


def read_instance_file(file_path):
    if os.path.isfile(file_path):
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    else:
        default_data = {"api-client": 1, "api-admin": 1, "iris": 1}
        with open(file_path, "w") as json_file:
            json.dump(default_data, json_file)
        return default_data


def write_instance_file(file_path, data):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file)


def create_alert_message(alerts):
    message = ""
    for alert in alerts:
        delta = alert[1] - alert[2]
        change = "증가하였습니다" if delta > 0 else "감소하였습니다"
        message += f"{alert[0]} 인스턴스가 {abs(delta)}개 {change}: {alert[2]}개 -> {alert[1]}개\n"
    return message


def send_alert(message):
    payload = {
        "title": "인스턴스 개수 변경 알림",
        "text": message.replace("\n", "<br>"),
    }
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except requests.RequestException as e:
        print(f"Failed to send alert: {e}")


if __name__ == "__main__":
    print("Start check instance")

    file_path = "instance.json"
    before_data = read_instance_file(file_path)

    while True:
        # 데이터 수집
        try:

            data = get_instance_counts()
            alerts = []
            print("현재 시간: ", datetime.datetime.now())

            # Prometheus에서 데이터를 가져온 경우 & 이전 데이터와 다른 경우
            for key, value in data.items():
                if value != before_data[key]:
                    alerts.append((key, value, before_data[key]))
                    before_data[key] = value

            if alerts:
                write_instance_file(file_path, before_data)
                message = create_alert_message(alerts)
                send_alert(message)

        except Exception as e:
            print(f"Error: {e}")

        # 1분마다 데이터 수집
        time.sleep(60)
