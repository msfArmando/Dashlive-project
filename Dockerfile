FROM python
WORKDIR /dashboards.py
COPY . /dashboards.py
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python3", "dashboards.py"]