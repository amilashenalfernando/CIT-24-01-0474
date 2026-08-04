# CCS3308 — Lab 6: Kubernetes Fundamentals with Minikube

This repository contains the completed manifests, answers, and visual proof for Lab 6 (Kubernetes Fundamentals with Minikube).

## Project Structure

```
lab6/
├── k8s/
│   ├── pod-frontend.yaml
│   ├── deployment-frontend.yaml
│   ├── service-frontend.yaml
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── cache-deployment.yaml
│   ├── cache-service.yaml
│   ├── postgres-statefulset.yaml
│   └── postgres-service.yaml
├── screenshots/
│   ├── task1.1.png
│   ├── task2.1.png
│   ├── task3.1.png
│   ├── task4.1.png
│   ├── task5.1.png
│   ├── task6.1.png
│   ├── task7.1.png
│   ├── task7.2.png
│   ├── task8.1.png
│   ├── task9.1.png
│   └── task10.1.png
├── answers.md
└── README.md
```

## How to Run

1. **Start Minikube**:
   ```bash
   minikube start --driver=docker
   ```

2. **Apply all application manifests**:
   ```bash
   kubectl apply -f k8s/
   ```

3. **Verify Cluster State**:
   ```bash
   kubectl get all
   ```

4. **Access Frontend Service**:
   ```bash
   minikube service frontend --url
   ```

5. **Clean up Resources**:
   ```bash
   kubectl delete -f k8s/
   minikube stop
   ```
