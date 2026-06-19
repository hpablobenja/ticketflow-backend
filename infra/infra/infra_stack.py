from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class TicketFlowInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Red (VPC) Optimizada para no generar costos por NAT Gateways
        # Usamos subredes públicas
        vpc = ec2.Vpc(
            self, "TicketFlowVPC",
            max_azs=2,
            nat_gateways=0, # 0 NAT Gateways para evitar cobros de red fijos
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Security Groups (Grupos de Seguridad)
        ec2_sg = ec2.SecurityGroup(self, "EC2SecurityGroup", vpc=vpc, description="Allow SSH and Web traffic")
        rds_sg = ec2.SecurityGroup(self, "RDSSecurityGroup", vpc=vpc, description="Allow Postgres traffic")

        # Reglas de Acceso
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH from anywhere")
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(8000), "Allow Auth Service HTTP traffic")
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(8001), "Allow Booking Service HTTP traffic")
        
        # Permitir que la EC2 se conecte a la Base de Datos RDS
        rds_sg.add_ingress_rule(ec2_sg, ec2.Port.tcp(5432), "Allow EC2 to connect to Postgres")

        # 2. Base de Datos Relacional (AWS RDS PostgreSQL)
        postgres_db = rds.DatabaseInstance(
            self, "PostgresInstance",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO), # db.t3.micro (Gratis)
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[rds_sg],
            database_name="ticketflow_db",
            allocated_storage=20, # 20 GB de almacenamiento SSD 
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False
        )

        # 3. Servidor de Aplicaciones (AWS EC2)
        # Script automatizado para instalar Docker y Docker Compose al encender la máquina
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "sudo apt-get update -y",
            "sudo apt-get install -y docker.io git",
            "sudo systemctl start docker",
            "sudo systemctl enable docker",
            "sudo usermod -aG docker ubuntu",
            # Instalar Docker Compose v2
            "sudo mkdir -p /usr/local/lib/docker/cli-plugins/",
            "sudo curl -SL https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose",
            "sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose"
        )

        ec2_instance = ec2.Instance(
            self, "TicketFlowAppServer",
            vpc=vpc,
            # t2.micro o t3.micro según la región de AWS
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO), 
            machine_image=ec2.MachineImage.from_ssm_parameter("/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"),
            security_group=ec2_sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            user_data=user_data,
            # OPCIONAL: Si deseas conectarte por SSH convencional, crea una Key Pair en la consola de AWS e introduce su nombre aquí:
            # key_pair=ec2.KeyPair.from_key_pair_name(self, "MyKeyPair", "mi-clave-ssh")
        )

        CfnOutput(
            self, "DatabaseEndpoint",
            value=postgres_db.db_instance_endpoint_address,
            description="El DB_HOST para tu archivo .env"
        )

        CfnOutput(
            self, "EC2PublicIP",
            value=ec2_instance.instance_public_ip,
            description="La IP pública de tu servidor"
        )