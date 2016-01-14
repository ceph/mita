import jenkins
from pecan import conf


def jenkins_connection():
    jenkins_url = conf.jenkins['url']
    jenkins_user = conf.jenkins['user']
    jenkins_token = conf.jenkins['token']
    return jenkins.Jenkins(jenkins_url, jenkins_user, jenkins_token)
