# 📚 Digital Library Backend with CI/CD
> High-availability document search & delivery platform, built with FastAPI, PostgreSQL, and AWS.

![Demo GIF](docs/demo.gif)

---

## 🚀 Overview
The Digital Library Backend powers a university-scale online repository with role-based access control, fast search, and secure document delivery. Designed for **>99.95% uptime**, it integrates a robust CI/CD pipeline to deliver features quickly without compromising stability.

---

## ✨ Features
- **High Availability** — Multi-instance FastAPI services on AWS EC2 with Nginx reverse proxy.  
- **Secure Access** — RBAC for admins, contributors, and readers.  
- **Optimized Queries** — Sub-45ms P95 latency through schema redesign & index tuning.  
- **File Management** — S3 object storage with presigned URLs for secure uploads/downloads.  
- **Continuous Delivery** — Automated GitHub Actions pipelines with linting, tests, and deployment gates.  

---

## 🛠 Tech Stack
- **Backend:** FastAPI, Python  
- **Database:** PostgreSQL  
- **Storage:** AWS S3  
- **Infrastructure:** AWS EC2, Nginx, Docker, Terraform  
- **CI/CD:** GitHub Actions  
- **Auth:** JWT with refresh tokens  
- **Monitoring:** AWS CloudWatch  

---

## 📐 Architecture
![Architecture Diagram](docs/architecture.png)

**Flow:**
1. User sends request → API Gateway (Nginx)  
2. FastAPI app handles request → PostgreSQL (metadata) + S3 (files)  
3. JWT-based RBAC middleware enforces permissions  
4. CI/CD automates build, test, deploy with rollback strategy  

---

## 📊 Key Results
- Delivered **>99.95% availability** for 25K+ users.  
- Reduced **P95 latency to <45ms** via database optimizations.  
- Cut post-deployment bugs by **45%** and doubled release frequency through automated CI/CD.  

---

## 📦 Local Setup
```bash
git clone https://github.com/<your-username>/digital-library-backend.git
cd digital-library-backend
docker compose up --build
