pipeline {
  agent {
    kubernetes {
      defaultContainer 'jnlp'
      yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
    - name: python
      image: python:3.11
      command:
        - cat
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    - name: kubectl
      image: bitnami/kubectl:latest
      command:
        - cat
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    - name: kaniko
      image: gcr.io/kaniko-project/executor:v1.23.2-debug
      command:
        - /busybox/cat
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker
        - name: workspace-volume
          mountPath: /home/jenkins/agent

  volumes:
    - name: docker-config
      secret:
        secretName: kaniko-docker-config
    - name: workspace-volume
      emptyDir: {}
"""
    }
  }

  environment {
    IMAGE = "dorraviv/url-shortener-platform"
    TAG = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Quality Checks') {
      steps {
        container('python') {
          sh '''
            pip install -r requirements-dev.txt
            flake8 app
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
            kubectl set image deployment/url-shortener \
            url-shortener=${IMAGE}:${TAG}

            kubectl rollout status deployment/url-shortener --timeout=120s
          '''
        }
      }
    }
  }
}

