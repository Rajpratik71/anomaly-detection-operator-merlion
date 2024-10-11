import kopf
import requests
import logging
from merlion.models import TimeSeries, Merlion, MerlionConfig

# Function to fetch metrics from different sources
def fetch_metrics(metric_source, metric_url, query, auth=None, bearer_token=None):
    headers = {}
    if bearer_token:
        headers['Authorization'] = f'Bearer {bearer_token}'

    if metric_source == 'prometheus':
        response = requests.get(f"{metric_url}?query={query}", auth=(auth['username'], auth['password']) if auth else None, headers=headers)
    elif metric_source == 'influxdb':
        response = requests.get(f"{metric_url}/query", params={"q": query}, auth=(auth['username'], auth['password']) if auth else None, headers=headers)
    # Add support for other metric sources here

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch metrics: {response.status_code} - {response.text}")

# Function to apply Merlion anomaly detection
def detect_anomalies(data):
    # Convert the data to TimeSeries for Merlion
    time_series = TimeSeries(data)

    # Initialize your Merlion model (configuration can vary based on your needs)
    model = Merlion(config=MerlionConfig())

    # Run anomaly detection
    anomalies = model.detect_anomalies(time_series)

    return anomalies

# Main reconciliation function
@kopf.on.create('anomalydetectors')
@kopf.on.update('anomalydetectors')
def reconcile_fn(spec, name, namespace, status, **kwargs):
    logging.info(f"Reconciling AnomalyDetector: {name}")

    anomaly_results = []

    # Loop through each metric defined in the CR
    for metric in spec.get('metrics', []):
        metric_source = metric.get('metricSource')
        metric_url = metric.get('metricURL')
        metric_query = metric.get('metricQuery')
        auth = metric.get('auth', {})

        # Extract authentication details
        bearer_token = auth.get('bearerToken')
        auth_credentials = {
            'username': auth.get('username'),
            'password': auth.get('password')
        }

        try:
            # Fetch the metrics for the current metric source
            metrics_data = fetch_metrics(metric_source, metric_url, metric_query, auth_credentials, bearer_token)

            # Assuming metrics_data contains the required structure for Merlion
            # Call the anomaly detection function
            anomalies = detect_anomalies(metrics_data)

            # Append results to anomaly_results
            anomaly_results.append({
                'metricQuery': metric_query,
                'anomalyResult': anomalies
            })

        except Exception as e:
            logging.error(f"Error fetching metrics for {metric_query}: {str(e)}")
            anomaly_results.append({
                'metricQuery': metric_query,
                'anomalyResult': f"Failed to fetch metrics: {str(e)}"
            })

    # Update the CR status with the anomaly detection results
    return {'anomalyResults': anomaly_results}

# Reconcile periodically or upon resume
@kopf.on.resume('anomalydetectors')
def resume_fn(spec, name, namespace, **kwargs):
    logging.info(f"Resuming AnomalyDetector reconciliation for: {name}")
    return reconcile_fn(spec, name, namespace, **kwargs)
