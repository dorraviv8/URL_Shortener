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
      image: alpine/k8s:1.30.2
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
              --context=dir://$PWD \
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
            # Apply all manifests except secrets — secrets are managed manually
            # to prevent overwriting live credentials with placeholder values.
            for f in $(find k8s/ -maxdepth 1 -name '*.yaml' ! -name 'secret*'); do
              kubectl apply -f "$f"
            done

            kubectl set image deployment/url-shortener \
              url-shortener=${IMAGE}:${TAG} -n default

            kubectl rollout status deployment/url-shortener -n default --timeout=300s
          '''
        }
      }
    }
  }

  post {
    success {
      echo "Pipeline succeeded: ${IMAGE}:${TAG} deployed"
    }
    failure {
      echo "Pipeline failed on branch ${env.BRANCH_NAME}, build #${env.BUILD_NUMBER}"
      container('kubectl') {
        sh '''
          echo "Rolling back deployment to previous version..."
          kubectl rollout undo deployment/url-shortener -n default
        '''
      }
    }
  }
}

