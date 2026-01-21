output "cluster_name" { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "ecr_syncshield" { value = aws_ecr_repository.syncshield.repository_url }
output "ecr_syncengage" { value = aws_ecr_repository.syncengage.repository_url }
