import grpc
import ltv_pb2
import ltv_pb2_grpc
import json

def run():
    channel = grpc.insecure_channel('127.0.0.1:50051')
    stub = ltv_pb2_grpc.LTVServiceStub(channel)

    request = ltv_pb2.LTVRequest(
        customer_id="user_1",
        recent_spend=55.0,
        engagement_score=0.8
    )

    response = stub.PredictLTV(request)

    print("Predicted LTV:", response.predicted_ltv)
    print("Confidence Score:", response.confidence_score)
    print("Explanation:", json.dumps(json.loads(response.explanation), indent=2))

if __name__ == "__main__":
    run()

