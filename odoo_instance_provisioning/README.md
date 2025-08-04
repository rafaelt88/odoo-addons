# Odoo Instance Provisioning Module

Module tự động hóa việc tạo và quản lý các instance Odoo độc lập cho từng khách hàng trong hệ thống SaaS.

## Chức năng chính

### 1. Tự động tạo Instance

- Nhận yêu cầu từ module "Cổng Đăng ký" qua API
- Tự động khởi tạo database PostgreSQL mới
- Deploy container Docker cho mỗi instance
- Cài đặt module theo gói dịch vụ đã chọn
- Thiết lập người dùng quản trị và thông tin công ty
- Cấu hình sub-domain và SSL

### 2. Quản lý Instance

- Khởi động/Dừng instance
- Backup tự động theo lịch
- Giám sát tài nguyên (CPU, RAM, Storage)
- Terminate instance khi không cần

### 3. API Endpoints

- `/api/provisioning/create_instance` - Tạo instance mới
- `/api/provisioning/request_status/<request_id>` - Kiểm tra trạng thái
- `/api/provisioning/instance_info/<subdomain>` - Thông tin instance
- `/api/provisioning/manage_instance/<subdomain>` - Quản lý instance
- `/api/provisioning/validate_subdomain` - Kiểm tra subdomain
- `/api/provisioning/plans` - Danh sách gói dịch vụ

### 4. Logging và Monitoring

- Log chi tiết quá trình provisioning
- Theo dõi lỗi và cảnh báo
- Thống kê sử dụng tài nguyên
- Dashboard quản lý

## Cài đặt

### 1. Quick Installation

Sử dụng script tự động:

```bash
# Option 1: Test dependencies first
cd addons/odoo_instance_provisioning/scripts
python test_dependencies.py

# Option 2: Auto-install dependencies (Bash - Linux/Mac)
chmod +x install_dependencies.sh
./install_dependencies.sh

# Option 3: Auto-install dependencies (Python - Cross-platform)
python install_dependencies.py
```

### 2. Manual Installation

#### Python Dependencies (Required)

```bash
pip install psycopg2-binary
pip install requests
```

#### Optional Dependencies

```bash
# For Docker container management (optional)
pip install docker

# For advanced monitoring (optional)
pip install prometheus-client
```

### 3. System Requirements

- Docker CE/EE
- PostgreSQL 12+
- Nginx/Apache (cho reverse proxy)

### 3. Installation

1. Copy module vào thư mục addons
2. Cập nhật app list trong Odoo
3. Cài đặt module "Odoo Instance Provisioning"
4. Cấu hình các parameters sau:

```python
# System Parameters
saas.base_domain = "yourdomain.com"
saas.docker_image = "odoo:17.0"
saas.backup_path = "/opt/odoo/backups"
saas.max_instances_per_plan = 100
```

## Cấu hình

### 1. Docker Configuration

Module sử dụng Docker để tạo container cho mỗi instance. Đảm bảo:

- Docker daemon đang chạy
- User Odoo có quyền truy cập Docker socket
- Network bridge được cấu hình đúng

### 2. Database Configuration

- PostgreSQL user 'odoo' có quyền tạo database
- Connection pooling được cấu hình phù hợp
- Backup storage có đủ dung lượng

### 3. Web Server Configuration (Nginx)

```nginx
server {
    listen 80;
    server_name *.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:$port;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Sử dụng

### 1. Tạo Instance qua API

```python
import requests

data = {
    "customer_email": "admin@company.com",
    "customer_name": "John Doe",
    "company_name": "My Company Ltd",
    "plan_id": 1,
    "subdomain": "mycompany",
    "admin_email": "admin@company.com"
}

response = requests.post(
    "http://your-odoo-server/api/provisioning/create_instance",
    json=data
)

result = response.json()
if result['success']:
    request_id = result['request_id']
    print(f"Instance request created: {request_id}")
```

### 2. Kiểm tra trạng thái

```python
response = requests.get(
    f"http://your-odoo-server/api/provisioning/request_status/{request_id}"
)

status = response.json()
print(f"Status: {status['data']['state']}")
```

### 3. Quản lý Instance

```python
# Start instance
requests.post(
    f"http://your-odoo-server/api/provisioning/manage_instance/mycompany",
    json={"action": "start"}
)

# Backup instance
requests.post(
    f"http://your-odoo-server/api/provisioning/manage_instance/mycompany",
    json={"action": "backup"}
)
```

## Monitoring

### 1. Instance Health

Module tự động theo dõi:

- CPU usage
- Memory usage
- Storage usage
- Last activity
- Container status

### 2. Logs

Tất cả hoạt động được log với các mức:

- `debug`: Thông tin debug
- `info`: Thông tin thông thường
- `warning`: Cảnh báo
- `error`: Lỗi
- `critical`: Lỗi nghiêm trọng

### 3. Alerts

System sẽ gửi cảnh báo khi:

- Instance down
- Resource usage cao
- Backup failed
- Provisioning failed

## Troubleshooting

### 1. Dependency Issues

#### "Python library not installed: docker"

```bash
# Install Docker Python library
pip install docker --user

# Or run the dependency installer
python3 scripts/install_dependencies.py
```

#### "Python library not installed: psycopg2"

```bash
# Install PostgreSQL adapter (note: install psycopg2-binary but import as psycopg2)
pip install psycopg2-binary --user

# On Ubuntu/Debian, if above fails, you might need:
sudo apt-get install python3-dev libpq-dev
pip install psycopg2 --user

# Test the installation
python -c "import psycopg2; print('psycopg2 OK')"
```

#### "Python library not installed: requests"

```bash
# Install requests library
pip install requests --user
```

#### Module installation fails

1. **Check dependency naming**: Odoo checks import names, not package names:

   - Install: `pip install psycopg2-binary`
   - Import: `import psycopg2` ✅
   - Install: `pip install requests`
   - Import: `import requests` ✅

2. Check Odoo logs: `/var/log/odoo/odoo.log`
3. Verify Python environment:
   ```bash
   python -c "import psycopg2; print('psycopg2 OK')"
   python -c "import requests; print('requests OK')"
   ```
4. Restart Odoo server after installing dependencies
5. Update app list in Odoo

### 2. Provisioning Failed

- Kiểm tra Docker service status
- Verify PostgreSQL connection
- Check available disk space
- Review instance logs

### 3. Container Issues

```bash
# Check container status
docker ps -a | grep odoo_

# View container logs
docker logs <container_id>

# Restart container
docker restart <container_id>
```

### 4. Database Issues

```bash
# Check database exists
sudo -u postgres psql -l | grep <db_name>

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='<db_name>'"
```

### 5. Permission Issues

#### Docker access denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again

# Or run with sudo (not recommended for production)
sudo docker ps
```

#### PostgreSQL access denied

```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Check odoo user permissions
sudo -u postgres psql -c "\du odoo"
```

## Architecture

### 1. Components

- **SaasInstance**: Model quản lý instance
- **SaasInstanceRequest**: Model quản lý yêu cầu tạo instance
- **SaasInstanceLog**: Model lưu logs
- **ProvisioningAPIController**: API endpoints
- **Scripts**: Bash scripts cho database operations

### 2. Workflow

1. API nhận yêu cầu tạo instance
2. Tạo SaasInstanceRequest record
3. Validate input data
4. Tạo SaasInstance record
5. Background job provisions instance:
   - Create database
   - Deploy container
   - Install modules
   - Setup admin user
   - Configure subdomain
6. Update instance status
7. Notify customer management module

### 3. Security

- API authentication
- Input validation
- SQL injection protection
- Container isolation
- Network security

## Performance

### 1. Scalability

- Horizontal scaling với multiple Odoo instances
- Load balancing cho API requests
- Database connection pooling
- Container orchestration với Kubernetes

### 2. Optimization

- Async provisioning
- Resource limits per instance
- Cleanup old data
- Monitoring resource usage

## Support

### 1. Logs Location

- Odoo logs: `/var/log/odoo/`
- Instance logs: Database table `saas_instance_log`
- Container logs: `docker logs <container_id>`

### 2. Backup Location

- Database backups: `/opt/odoo/backups/`
- Filestore backups: `/opt/odoo/backups/`

### 3. Configuration Files

- Odoo config: `/etc/odoo/odoo.conf`
- Nginx config: `/etc/nginx/sites-available/`
- Docker compose: `docker-compose.yml`

## License

LGPL-3

## Tránh xung đột Model

Module này sử dụng tên model riêng để tránh xung đột với module khác:

- `saas.instance.provisioning` (thay vì `saas.instance`)
- `saas.instance.provisioning.log` (thay vì `saas.instance.log`)

Điều này đảm bảo module có thể hoạt động song song với module `saas_customer_management` mà không gây xung đột.

## Cài đặt
