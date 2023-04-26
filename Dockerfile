FROM python:3.7-bullseye
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "finder/main.py"]