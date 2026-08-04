# Lab 6 — Answers to Checkpoint Questions

## Task 1.2: Pod to Component Table

| Observed Pod Name | Component Represented | Role / Tier |
| :--- | :--- | :--- |
| `etcd-minikube` | etcd | Control Plane (Consistent & highly-available key-value store) |
| `kube-apiserver-minikube` | API Server | Control Plane (Exposes Kubernetes API, front-end for control plane) |
| `kube-controller-manager-minikube` | Controller Manager | Control Plane (Runs controller loops like ReplicaSet & Node controllers) |
| `kube-scheduler-minikube` | Scheduler | Control Plane (Assigns newly created pods to worker nodes) |
| `kube-proxy-xxxxx` | kube-proxy | Worker Node (Maintains network rules on nodes for communication) |
| `storage-provisioner` / `coredns` | Storage / DNS Addons | Cluster Addons |

### Component NOT appearing as a Pod:
* **`kubelet`** and the **Container Runtime (Docker/containerd)** do NOT appear as pods in `kube-system`.
* **Reason:** `kubelet` is the node agent that runs directly as a system daemon on the operating system host. Since `kubelet` is responsible for starting and managing containers/pods on a node, it cannot run inside a pod itself.

---

## Checkpoint Q1: Control Plane vs. Worker Node
* **Control Plane:** The "brain" of the Kubernetes cluster. It is responsible for global cluster management, making decisions (e.g., scheduling pods, scaling, rolling updates), detecting events, and maintaining cluster state.
* **Worker Node:** The "worker" machine in the cluster. It hosts and executes containerized application workloads (Pods) as instructed by the Control Plane, managing container execution, local networking, and proxying.

---

## Checkpoint Q2: Ephemeral Pods and IP Addresses
* **Has the IP changed?** Yes, after deleting `pod-frontend` and recreating it, its IP address changed.
* **Explanation:** Pods in Kubernetes are **ephemeral** (disposable and temporary). They are created, assigned a dynamic internal IP from the node's CIDR range, destroyed, and recreated with new IP addresses. You should never rely on hardcoded Pod IP addresses.

---

## Checkpoint Q3: Control-Loop Model for Self-Healing
When a pod managed by a Deployment is deleted, Kubernetes executes the following control loop steps:
1. **Desired State:** The Deployment specifies a desired state of **3 replicas** of `frontend`.
2. **Controller Watches:** The ReplicaSet controller continuously monitors the cluster status via the API server.
3. **Actual State:** Upon pod deletion, the actual state drops to **2 running pods**.
4. **Gap Detected:** The controller compares Actual (2) vs Desired (3) and detects a gap (`3 != 2`).
5. **Reconcile:** The controller immediately requests the scheduler to create a new pod replacement, restoring the actual count back to 3.

---

## Checkpoint Q4: Independent Scaling of Decoupled Tiers
* Application tiers are completely decoupled using **Kubernetes Services** (`api-service`, `cache-service`, `postgres-service`).
* Lower tiers interact through static cluster DNS names / ClusterIP addresses rather than direct pod IPs.
* Scaling the frontend deployment up or down adds or removes frontend pod endpoints behind `service-frontend` without modifying or affecting backend database/API configurations or state.

---

## Checkpoint Q5: Port-Forward vs. Kubernetes Service
* **`kubectl port-forward`:** A developer debugging tool that establishes a direct local tunnel to a single, specific pod endpoint. If that pod crashes or terminates, the tunnel breaks.
* **Kubernetes Service:** A high-level cluster abstraction that provides a single, stable IP/DNS entry and automatic load balancing across dynamic sets of ephemeral pods using label selectors (`app: frontend`). Services abstract away pod IP changes.

---

## Checkpoint Q6: Rolling Updates & Rollbacks vs. Docker Compose
* **Docker Compose:** Lacks native zero-downtime rolling updates. Updating an image typically requires stopping containers before starting new ones, resulting in application downtime. Compose does not natively track rollout status or support instant one-command atomic rollbacks (`kubectl rollout undo`).
* **Kubernetes:** Automatically handles zero-downtime rolling updates by incrementally creating new pods before terminating old ones, continually monitoring health probes, and allowing instant automated rollbacks if an update fails.

---

## Checkpoint Q7: Deployment vs. StatefulSet
* **Deployment (Stateless - Frontend / API):** Pods are identical, interchangeable, and disposable. They receive random hashes in their names (e.g., `frontend-74c47b59-abcde`), share no persistent storage, and can be started/stopped in any order.
* **StatefulSet (Stateful - Database / Postgres):** Pods have sticky, persistent identities (`postgres-0`), deterministic ordered startup/shutdown, and are each attached to specific persistent volume claims (`PVC`). If `postgres-0` dies, its replacement pod retains the exact same network identity and re-attaches to the exact same storage volume.

---

## Checkpoint Q8: Data Persistence and PersistentVolumeClaim
* **Would data survive without a PVC?** No, the data would NOT have survived.
* **Explanation:** Without a `PersistentVolumeClaim` (PVC), postgres storage would rely on emptyDir or host ephemeral container layers. When `postgres-0` is deleted, its container root filesystem is completely destroyed, wiping out all PostgreSQL data files.

---

## Checkpoint Q9: Broken Pod Status and Pod Status Table
* **Status Observed:** `ErrImagePull` / `ImagePullBackOff`.
* **Pod Status Table Comparison:** This status is related to **`Pending`** / Container Creation Failure. It is not listed as a final execution state because the pod cannot transition to `Running`.
* **Meaning:** The container runtime attempted to pull `nginx:definitely-not-a-real-tag` from Docker Hub, but the image repository returned a "404 Not Found" error. Kubernetes enters an exponential backoff loop retrying the image pull.
