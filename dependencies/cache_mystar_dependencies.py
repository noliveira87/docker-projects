from dataclasses import dataclass
from ensurepip import version
from typing import List
import requests
import json
import os
import certifi

@dataclass
class Dependency:
    group_id: str
    artifact_id: str
    version: str

    def to_string(self) -> str:
        return f"{self.group_id}:{self.artifact_id}:{self.version}"

DIR = "files"

ARTIFACTORY = "https://artifactory.softwarefactory.cloud.corpintra.net/artifactory"
RISING_STARS_REPO = "ris-maven-local"
MY_STAR_REPO = "mystar-android"
ECOMMERCE_REPO = "ecommerce-sdk-android-maven-local"
MAVEN_VIRTUAL_REPO = "public-maven-repos-virtual"

JFROG_TOKEN = os.environ.get('JFROG_API_KEY')
JFROG_HEADERS = {"X-JFrog-Art-Api": JFROG_TOKEN}

CERTIFICATE = "softwarefactory.detss.corpintra.net.cer"

RISING_STARS_DEPENDENCY_LIST = [
    Dependency(group_id="com.daimler.mm", artifact_id="mb-bluetooth-link", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBAppFamily", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBLoggerKit", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBMobileSDK", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBReachMeKit", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBUIKit", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="MBSupportKit", version=""),
    Dependency(group_id="com.daimler.mm", artifact_id="PrivacyCenter", version="")
]
MY_STAR_DEPENDENCY_LIST = [
    Dependency(group_id="com.daimler", artifact_id="mmparkinglib", version=""),
    Dependency(group_id="com.heremap", artifact_id="sdk", version=""),
    Dependency(group_id="com.daimler.payment", artifact_id="bertha-sdk", version="")
]
ECOMMERCE_DEPENDENCY_LIST = [
    Dependency(group_id="com.daimler.sdk", artifact_id="ecommerce", version=""),
    Dependency(group_id="com.daimler.sdk", artifact_id="ecommerce-ui", version="")
]
VIRTUAL_REPOS_DEPENDENCY_LIST = [
    Dependency(group_id="it.macisamuele", artifact_id="calendarprovider-lib", version=""),
    Dependency(group_id="com.shawnlin", artifact_id="number-picker", version=""),
    Dependency(group_id="moe.banana", artifact_id="moshi-jsonapi-retrofit-converter", version="")
]

NEXUS_BASE_URL = "https://nexus.euc1.cicd.oneweb.mercedes-benz.com"
NEXUS_REPO = "public-releases"
NEXUS_USERNAME=os.environ.get('NEXUS_USERNAME')
NEXUS_PASSWORD=os.environ.get('NEXUS_PASSWORD')
NEXUS_AUTH = (NEXUS_USERNAME, NEXUS_PASSWORD)

def get_jfrog_deps(dependency_list: List[Dependency], repo: str):
    jfrog_list = []

    for dep in dependency_list:
        # find all versions for the current dependency
        url = f"{ARTIFACTORY}/api/search/versions?g={dep.group_id}&a={dep.artifact_id}&repos={repo}"
        results = requests.get(url, headers=JFROG_HEADERS, verify=CERTIFICATE).json()["results"]
        versions = list(map(lambda x: x["version"], results))

        # skip snapshot and debug builds
        versions_filtered = list(filter(lambda x: "SNAPSHOT" not in x and "debug" not in x, versions))

        # take last 25 versions to not blow the Nexus storage
        versions_latest = versions_filtered[0:25]

        # put all the versions into the dependency list
        for ver in versions_latest:
            jfrog_list.append(Dependency(group_id=dep.group_id, artifact_id=dep.artifact_id, version=ver))

    return jfrog_list

def get_nexus_deps(dependency_list):
    nexus_list = []

    for dep in dependency_list:
        # find all versions for the current dependency
        url = f"{NEXUS_BASE_URL}/service/rest/v1/search?repository={NEXUS_REPO}&group={dep.group_id}&name={dep.artifact_id}"
        items = requests.get(url, auth=NEXUS_AUTH).json()["items"]

        # put all the versions into the dependency list
        for it in items:
            nexus_list.append(Dependency(group_id=it["group"], artifact_id=it["name"], version=it["version"]))

    return nexus_list

def cache_dependency_list(mystar_list: List[Dependency], nexus_list: List[Dependency], jfrog_repo: str):
    for d in mystar_list:
        # specify which files we are looking for
        file_names = [
            f"{d.artifact_id}-{d.version}.pom",
            f"{d.artifact_id}-{d.version}.aar",
            f"{d.artifact_id}-{d.version}.jar",
            f"{d.artifact_id}-{d.version}-kdoc.jar",
            f"{d.artifact_id}-{d.version}-sources.jar",
            f"{d.artifact_id}-{d.version}-javadoc.jar"
        ]

        if d not in nexus_list:
            print(f"{d.to_string()} NOT CACHED")

            for file_name in file_names:
                group_id = d.group_id.replace(".", "/")
                download_url = f"{ARTIFACTORY}/{jfrog_repo}/{group_id}/{d.artifact_id}/{d.version}/{file_name}"
                print(download_url)

                # download dependency from JFrog
                response = requests.get(download_url, headers=JFROG_HEADERS, verify=CERTIFICATE)
                print(response.status_code)

                # store it locally
                file_path = f"{DIR}/{file_name}"
                if response.status_code == 200:
                    open(file_path, "wb").write(response.content)

                    # upload to Nexus
                    upload_url = f"{NEXUS_BASE_URL}/repository/{NEXUS_REPO}/{group_id}/{d.artifact_id}/{d.version}/{file_name}"
                    requests.put(upload_url, data=open(file_path, "rb"), auth=NEXUS_AUTH)

                    # cleanup. so far it is disabled and Nexus works as an additional backup
                    # os.remove(file_path)
        else:
            print(f"{d.to_string()} CACHED")

def cache(list: List[Dependency], repo: str):
    jfrog_list = get_jfrog_deps(list, repo)
    nexus_list = get_nexus_deps(list)
    cache_dependency_list(jfrog_list, nexus_list, repo)

def main():
    if not os.path.exists(DIR):
        os.mkdir(DIR)

    # cache dependencies from RisingStars repo
    cache(RISING_STARS_DEPENDENCY_LIST, RISING_STARS_REPO)

    # cache dependencies from MyStar repo
    cache(MY_STAR_DEPENDENCY_LIST, MY_STAR_REPO)

    # cache dependencies from Ecommers repo
    cache(ECOMMERCE_DEPENDENCY_LIST, ECOMMERCE_REPO)
    
    # cache dependencies from Virtual Maven repo
    cache(VIRTUAL_REPOS_DEPENDENCY_LIST, MAVEN_VIRTUAL_REPO)

main()
