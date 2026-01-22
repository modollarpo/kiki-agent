
import grpc
import ltv_pb2
import ltv_pb2_grpc
import json

def run_tests():
    test_cases = [
        {"customer_id": "user_1", "recent_spend": 55.0, "engagement_score": 0.8},
        {"customer_id": "user_2", "recent_spend": 120.5, "engagement_score": 0.5},
        {"customer_id": "user_3", "recent_spend": 0.0, "engagement_score": 1.0},
        {"customer_id": "user_4", "recent_spend": 300.0, "engagement_score": 0.2},
        {"customer_id": "user_5", "recent_spend": 75.0, "engagement_score": 0.0},
        {"customer_id": "user_6", "recent_spend": -10.0, "engagement_score": 0.7},  # Edge case: negative spend
        {"customer_id": "user_7", "recent_spend": 50.0, "engagement_score": 1.5},   # Edge case: engagement > 1
    ]

    try:
        channel = grpc.insecure_channel('127.0.0.1:50051')
        stub = ltv_pb2_grpc.LTVServiceStub(channel)
        for i, case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {case}")
            request = ltv_pb2.LTVRequest(
                customer_id=case["customer_id"],
                recent_spend=case["recent_spend"],
                engagement_score=case["engagement_score"]
            )
            try:
                response = stub.PredictLTV(request, timeout=2)
                print("Predicted LTV:", response.predicted_ltv)
                print("Confidence Score:", response.confidence_score)
                try:
                    explanation = json.loads(response.explanation)
                    print("Explanation:", json.dumps(explanation, indent=2))
                except Exception as ex:
                    print("Explanation parsing error:", ex)
            except grpc.RpcError as rpc_ex:
                print(f"gRPC error: {rpc_ex.code()} - {rpc_ex.details()}")
    except Exception as ex:
        print("Failed to connect to SyncValue gRPC server:", ex)

if __name__ == "__main__":
    run_tests()

