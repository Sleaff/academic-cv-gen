#!/bin/bash

# Start Backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start Frontend
streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0