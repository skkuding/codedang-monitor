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


def fetch_metrics(query):
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        return None


if __name__ == "__main__":
    print("Start check instance")

    file_path = "instance.json"

    if os.path.isfile(file_path):
        print(f"{file_path} exists.")
    else:  # 인스턴스 개수를 기록하는 파일이 없으면 생성 (기본값: 1)
        print(f"{file_path} does not exist.")
        with open("instance.json", "w") as json_file:
            data = {"api-client": 1, "api-admin": 1, "iris": 1}
            json.dump(data, json_file)

    while True:
        # 데이터 수집
        try:
            backend_client_metric_query = 'count by (instance) (group(system_cpu_utilization{job="backend-client-metric"}))'
            result_api_client = fetch_metrics(backend_client_metric_query)
            backend_admin_metric_query = 'count by (instance) (group(system_cpu_utilization{job="backend-admin-metric"}))'
            result_api_admin = fetch_metrics(backend_admin_metric_query)
            iris_metric_query = (
                'count by (instance) (group(cpu_usage_percent{job="iris-metric"}))'
            )
            result_iris = fetch_metrics(iris_metric_query)

            data = {}
            alerts = []
            print("현재 시간: ", datetime.datetime.now())

            # Prometheus에서 데이터를 가져온 경우만
            if result_api_client["data"]["result"]:
                result = result_api_client["data"]["result"][0]["value"][1]
                data["api-client"] = result
                print("Client 인스턴스 개수: ", (result))

            if result_api_admin["data"]["result"]:
                result = result_api_admin["data"]["result"][0]["value"][1]
                data["api-admin"] = result
                print("Admin 인스턴스 개수: ", (result))

            if result_iris["data"]["result"]:
                result = result_iris["data"]["result"][0]["value"][1]
                data["iris"] = result
                print("Iris 인스턴스 개수: ", (result))

            # 이전 데이터와 비교
            with open("instance.json", "r") as json_file:
                before_data = json.load(json_file)

            # Prometheus에서 데이터를 가져온 경우 & 이전 데이터와 다른 경우
            for key, value in data.items():
                print(key)
                if key == "api-client":
                    if data["api-client"] != before_data["api-client"]:
                        print("api-client 인스턴스 개수 변경")
                        alerts.append(
                            (
                                "Client API",
                                int(data["api-client"]),
                                int(before_data["api-client"]),
                            )
                        )
                        before_data["api-client"] = data["api-client"]
                if key == "api-admin":
                    if data["api-admin"] != before_data["api-admin"]:
                        print("api-admin 인스턴스 개수 변경")
                        alerts.append(
                            (
                                "Admin API",
                                int(data["api-admin"]),
                                int(before_data["api-admin"]),
                            )
                        )
                        before_data["api-admin"] = data["api-admin"]
                if key == "iris":
                    if data["iris"] != before_data["iris"]:
                        print("iris 인스턴스 개수 변경")
                        alerts.append(
                            ("Iris", int(data["iris"]), int(before_data["iris"]))
                        )
                        before_data["iris"] = data["iris"]

            if alerts:
                with open("instance.json", "w") as json_file:
                    json.dump(before_data, json_file)  # 변경된 인스턴스 개수 저장

                message = ""
                for alert in alerts:
                    if (alert[1] - alert[2]) > 0:
                        message += f"{alert[0]} 인스턴스가 {alert[1]-alert[2]}개 증가하였습니다: {alert[2]}개 -> {alert[1]}개\n"
                    else:
                        message += f"{alert[0]} 인스턴스 {alert[2]-alert[1]}개 감소하였습니다: {alert[2]}개 -> {alert[1]}개\n"
                payload = {
                    "title": "인스턴스 개수 변경 알림",
                    "text": message,
                }
                requests.post(WEBHOOK_URL, json=payload)

        except Exception as e:
            print(f"Error: {e}")

        # 1분마다 데이터 수집
        time.sleep(60)
