pipeline {
    agent any
    
    environment {
        APP_NAME = 'url-shortener'
        IMAGE_TAG = "${BUILD_NUMBER}"
        NETWORK_NAME = "test-net-${BUILD_NUMBER}"
        DOCKER_HOST = "tcp://dind:2375"
    }
    
    options {
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
                echo '[SUCCESS] Code checked out successfully!'
            }
        }
        
        stage('Create Test Network') {
            steps {
                echo 'Creating isolated Docker network for testing...'
                sh "docker network create ${NETWORK_NAME}"
                echo '[SUCCESS] Test network created!'
            }
        }
        
        stage('Start Database') {
            steps {
                echo 'Starting PostgreSQL database...'
                sh """
                    docker run -d \\
                        --name test-db-${BUILD_NUMBER} \\
                        --network ${NETWORK_NAME} \\
                        -e POSTGRES_DB=shortener \\
                        -e POSTGRES_USER=user \\
                        -e POSTGRES_PASSWORD=password \\
                        postgres:15-alpine
                """
                echo 'Waiting for database to be ready...'
                sh """
                    for i in {1..30}; do
                        if docker exec test-db-${BUILD_NUMBER} pg_isready -U user -d shortener; then
                            echo "[SUCCESS] Database is ready!"
                            break
                        fi
                        echo "Waiting for database... (\$i/30)"
                        sleep 2
                    done
                """
            }
        }
        
        stage('Build Image') {
            steps {
                script {
                    echo "Building Docker image: ${APP_NAME}:${IMAGE_TAG}"
                    docker.build("${APP_NAME}:${IMAGE_TAG}", ".")
                }
            }
        }
        
        stage('Test Image') {
            steps {
                script {
                    echo "Running containerized tests..."
                    
                    // Start the image in our test network
                    sh """
                        docker run -d \\
                            --name test-app-${BUILD_NUMBER} \\
                            --network ${NETWORK_NAME} \\
                            -e DATABASE_URL=postgresql://user:password@test-db-${BUILD_NUMBER}:5432/shortener \\
                            ${APP_NAME}:${IMAGE_TAG}
                    """
                    
                    // Wait for app to start
                    sh 'sleep 10'
                    
                    // Test health endpoint
                    echo 'Testing application health endpoint...'
                    sh "docker run --rm --network ${NETWORK_NAME} curlimages/curl -f http://test-app-${BUILD_NUMBER}:8000/ || exit 1"
                    
                    // Test API docs
                    echo 'Testing API documentation endpoint...'
                    sh "docker run --rm --network ${NETWORK_NAME} curlimages/curl -f http://test-app-${BUILD_NUMBER}:8000/docs || exit 1"
                    
                    // Test URL shortening
                    echo 'Testing URL shortening functionality...'
                    sh """
                        RESPONSE=\$(docker run --rm --network ${NETWORK_NAME} curlimages/curl -s -X POST http://test-app-${BUILD_NUMBER}:8000/shorten \\
                            -H "Content-Type: application/json" \\
                            -d '{"url": "https://example.com"}')
                        echo "Shorten response: \$RESPONSE"
                        if [[ ! "\$RESPONSE" =~ "short_url" ]]; then
                            echo "[ERROR] URL shortening failed"
                            exit 1
                        fi
                    """
                    
                    // Cleanup test containers
                    sh "docker stop test-app-${BUILD_NUMBER} || true"
                    sh "docker rm test-app-${BUILD_NUMBER} || true"
                    sh "docker stop test-db-${BUILD_NUMBER} || true"
                    sh "docker rm test-db-${BUILD_NUMBER} || true"
                }
            }
        }
        
        stage('Cleanup Network') {
            steps {
                echo 'Cleaning up test network...'
                sh "docker network rm ${NETWORK_NAME} || true"
                echo '[SUCCESS] Cleanup complete!'
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up resources...'
            sh """
                docker stop test-app-${BUILD_NUMBER} test-db-${BUILD_NUMBER} 2>/dev/null || true
                docker rm test-app-${BUILD_NUMBER} test-db-${BUILD_NUMBER} 2>/dev/null || true
                docker network rm ${NETWORK_NAME} 2>/dev/null || true
            """
        }
        success {
            echo "[SUCCESS] PIPELINE SUCCESSFUL!"
            echo "Built and tested: ${APP_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo '[ERROR] Pipeline failed. Check the logs above.'
            echo 'Dump container logs for debugging:'
            sh """
                echo "=== Application logs ==="
                docker logs test-app-${BUILD_NUMBER} 2>/dev/null || echo "No app container logs"
                echo "=== Database logs ==="
                docker logs test-db-${BUILD_NUMBER} 2>/dev/null || echo "No db container logs"
            """
        }
    }
}