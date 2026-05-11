output "dashboard_url" {
  value = "http://${aws_instance.streamlit_server.public_ip}:8501"
}