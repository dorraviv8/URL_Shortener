pipeline {
  agent {
    kubernetes {
      inheritFrom 'kaniko'
      defaultContainer 'jnlp'
    }
  }

  environment {
    IMAGE = "dorraviv/url-shortener-platform"
    TAG   = "${env.BUILD_NUMBER}"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Lint') {
      steps {
        container('python') {
          sh '''
            pip install -r app/requirements.txt
            flake8 app
          '''
        }
      }
    }

    stage('Run Tests') {
      steps {
        container('python') {
          sh '''
            pip install -r app/requirements.txt
            export PYTHONPATH=$PWD
            pytest -v
          '''
        }
      }
    }

    stage('Build & Push (Kaniko)') {
      steps {
        container('kaniko') {
          sh '''
            /kaniko/executor \
              --dockerfile=Dockerfile \
              --context=$PWD \
              --destination=${IMAGE}:${TAG} \
              --destination=${IMAGE}:latest \
              --verbosity=info
          '''
        }
      }
    }

stage('Deploy to Kubernetes') {
  when {
    branch 'main'
  }

  steps {
    container('python') {
      sh '''
        kubectl set image deployment/url-shortener \
        url-shortener=${IMAGE}:${TAG} \
        -n default

        kubectl rollout status deployment/url-shortener -n default
      '''
    }
  }
}