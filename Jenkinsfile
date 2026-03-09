pipeline {
  agent {
    kubernetes {
      inheritFrom 'kaniko'
      defaultContainer 'jnlp'
      yaml """
spec:
  containers:
  - name: python
    image: python:3.11
    command:
    - cat
    tty: true

  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
"""
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
            pip install flake8
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
            export PYTHONPATH=$PWD/app
            pytest -v
          '''
        }
      }
    }

    stage('Build & Push Image') {
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
      steps {
        container('kubectl') {
          sh '''
            kubectl apply -f k8s/
            kubectl rollout restart deployment/url-shortener
            kubectl rollout status deployment/url-shortener
          '''
        }
      }
    }

  }
}