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
          "name": "ps_main",
          "type": "postgres",
          "host": "postgres-svc",
          "port": 5432,
          "user": "user",
          "password": "password",
          "dbname": "mydb"
        },
        {
          "name": "mysql_userdb",
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
          "name": "redis_cache",
          "type": "redis",
          "host": "redis-svc",
          "port": 6379
        }
      ],
      "search_checks": [
        {
          "name": "es_cluster",
          "type": "elasticsearch",
          "url": "http://elasticsearch-svc:9200"
        }
      ],
      "storage_checks": [
        {
          "name": "s3_assetsbucket",
          "type": "s3",
          "bucket_name": "my-prod-assets",
          "region": "us-east-1"
        }
      ],
      "vendors_endpoints": [
        {
          "name": "gh_com_public",
          "type": "http_get",
          "url": "https://github.com",
          "timeout": 5
        },
        {
          "name": "sentry_io_public",
          "type": "http_get",
          "url": "https://sentry.io",
          "timeout": 5
        }
      ]
    }
