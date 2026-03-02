pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Building Docker image...'
                sh 'docker version'
            }
        }

        stage('Push') {
            steps {
                echo 'Pushing Docker image...'
            }
        }
    }
}
