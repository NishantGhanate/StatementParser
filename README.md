 source venv/bin/activate

uvicorn main:app --host 0.0.0.0 --port 8000 --reload


http://localhost:8000/docs


If you wanto connect to service outside docker
$ hostname -I
$ 192.168.153.156


┌─────────────────────────────────────────────────────────┐
│                    Windows Host                         │
│                   192.168.0.152                         │
│                                                         │
│  ┌─────────────────┐      ┌────────────────────────┐    │
│  │  Docker Desktop │      │         WSL            │    │
│  │                 │      │    192.168.144.x       │    │
│  │  ┌───────────┐  │      │                        │    │
│  │  │   n8n     │  │  ?   │  ┌─────────────────┐   │    │
│  │  │ container │◄─┼──────┼──│ FastAPI :8000   │   │    │
│  │  └───────────┘  │      │  └─────────────────┘   │    │
│  └─────────────────┘      └────────────────────────┘    │
└─────────────────────────────────────────────────────────┘


# Start
docker-compose up -d

# Logs
docker-compose logs -f celery_worker
