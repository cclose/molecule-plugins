# KubeVirt Driver 

## RoadMap

### Harvester Integration

The driver is actually developed against a Harvester Cluster, SUSE Rancher's distribution of KubeVirt,
and works as-is, but a few of the items needed to make it work are less-than-intuitive, so i'd like
to add some features that make harvester clusters easier to work with, such as:
- Sourcing rootFsStorageClass from harvester image name
- Sourcing networking settings from harvester vm network

### KubeVirt Features

- Support for DataVolumes and Container Disks
- Support for "Raw Yaml Mode" where an expert can directly template hte yaml they want
- Support for more sophisicated connection options, like an SSH Service or Ingress?

### Helm Integration

When I was 80% of the way through, I realized it'd probably make more sense and be more Kube native if
we used a helm chart to deploy, manage, and destroy the instances instead of the kubernetes.core 
ansible module, but maybe we want to leave it as-is and add helm support as a feature gate?

Items available from Helm mode:
- Support for "additional manifest" to let people writ their own helm templates and have them auto-included