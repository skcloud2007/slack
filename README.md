# slack
Slack integration for notifications and making some actions

# Webhook URLs for Your Workspace
```bash
curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
# skm_alerts
```bash
https://hooks.slack.com/services/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XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```



# Run Jenkins in Docker on Windows
### If you use Docker Desktop, you can spin up Jenkins quickly:

```bash
docker network create jenkins
docker run -d --name jenkins \
  --network jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts
```

```bash
Open http://localhost:8080, then get the initial password from logs:
docker logs jenkins


[LF]> Jenkins initial setup is required. An admin user has been created and a password generated.
[LF]> Please use the following password to proceed to installation:
[LF]>
[LF]> 1c15193c4bf34e42be9c766482cbc650
[LF]>
[LF]> This may also be found at: /var/jenkins_home/secrets/initialAdminPassword
[LF]>
[LF]> *************************************************************
[LF]> *************************************************************
[LF]> *************************************************************

```


