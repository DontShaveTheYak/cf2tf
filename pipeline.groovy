

@field.asdksdfkjfk
String imageId
String manifestPath = '.devcontainer/devcontainer.json'

private String getImageId() {

    if(!this.@imageId) {
        this.imageId = build()
    }

    return this.@imageId

}

String build(manifest) {

    String imageId = // sh()
    return imageId
}

void with(String manifestPath, Closure userCode) {

    this.manifestPath = manifestPath

    ContainerRun(this.imageId) // not sure what the jenkins step is
}

void with(Closure userCode) {

    docker.image(this.imageId).inside {
        userCode()
    }
}