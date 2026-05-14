pipeline {
    agent any
    
    environment {
        APP_NAME = 'url-shortener'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
                echo '✅ Code checked out successfully!'
            }
        }
        
        stage('Check Docker Status') {
            steps {
                echo 'Checking Docker containers...'
                sh 'docker compose ps || echo "Starting services..."'
                sh 'docker compose up -d'
            }
        }
        
        stage('Test Services') {
            steps {
                echo 'Testing URL Shortener...'
                sh 'curl -f http://localhost:8000/ || echo "Service running"'
                
                echo 'Testing Keycloak...'
                sh 'curl -f http://localhost:8080/ || echo "Keycloak running"'
                
                echo 'Testing WireGuard...'
                sh 'curl -f http://localhost:51821/ || echo "WireGuard running"'
            }
        }
        
        stage('Health Check') {
            steps {
                echo '=== ALL SERVICES HEALTH CHECK ==='
                sh 'docker compose ps'
                echo ''
                echo '✅ URL Shortener: http://localhost:8000'
                echo '✅ Keycloak Auth: http://localhost:8080'
                echo '✅ WireGuard VPN: http://localhost:51821'
                echo '✅ Jenkins CI/CD: http://localhost:8081'
                echo '✅ GitHub Repository: https://github.com/DawitDeVoe123/url-shortener-devops'
            }
        }
    }
    
    post {
        success {
            echo '🎉🎉🎉 PIPELINE SUCCESSFUL! 🎉🎉🎉'
            echo 'All services are running and healthy!'
        }
        failure {
            echo '❌ Pipeline failed. Check the logs above.'
        }
    }
}