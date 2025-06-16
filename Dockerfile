FROM python
WORKDIR /dashboards.py
COPY . /dashboards.py
CMD ["python3", "dashboards.py"]