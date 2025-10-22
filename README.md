# uptime-measures
uptime-measures

# sample
apiVersion: v1
kind: ConfigMap
metadata:
  name: healthcheck-config
  namespace: test
data:
  HEALTH_CHECK_CONFIG: |
    {
      "database_checks": [
        {
          "name": "PostgreSQL-Main",
          "type": "postgres",
          "host": "postgres-svc",
          "port": 5432,
          "user": "user",
          "password": "password",
          "dbname": "mydb"
        },
        {
          "name": "MySQL-UserDB",
          "type": "mysql",
          "host": "mysql-svc",
          "port": 3306,
          "user": "user",
          "password": "password",
          "database": "userdb"
        }
      ],
      "caching_checks": [
        {
          "name": "Redis-Cache",
          "type": "redis",
          "host": "redis-svc",
          "port": 6379
        }
      ],
      "search_checks": [
        {
          "name": "Elasticsearch-Cluster",
          "type": "elasticsearch",
          "url": "http://elasticsearch-svc:9200"
        }
      ],
      "storage_checks": [
        {
          "name": "S3-AssetsBucket",
          "type": "s3",
          "bucket_name": "my-prod-assets",
          "region": "us-east-1"
        }
      ],
      "vendors_endpoints": [
        {
          "name": "GitHub.com-Public",
          "type": "http_get",
          "url": "https://github.com",
          "timeout": 5
        },
        {
          "name": "Sentry.io-Public",
          "type": "http_get",
          "url": "https://sentry.io",
          "timeout": 5
        }
      ]
    }
