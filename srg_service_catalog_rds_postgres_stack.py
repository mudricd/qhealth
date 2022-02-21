from aws_cdk import core
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_rds as _rds
from aws_cdk import cloudformation_include as _cloudformation_include


class SrgServiceCatalogRdsPostgresStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Importing VPC
        vpc = _ec2.Vpc.from_vpc_attributes(self, "ImportedVpc", 
                                           vpc_id= core.Fn.import_value('VPC-ID'),
                                           availability_zones=["ap-southeast-2a","ap-southeast-2b","ap-southeast-2c"],
                                           public_subnet_ids=[core.Fn.import_value("ApplicationSubnetAzC"), core.Fn.import_value("ApplicationSubnetAzB"),core.Fn.import_value("ApplicationSubnetAzA")]
                                           )

        subnetid1=_ec2.Subnet.from_subnet_attributes(self, "subnetid1", availability_zone="ap-southeast-2a", subnet_id=core.Fn.import_value("ApplicationSubnetAzA"))
        subnetid2=_ec2.Subnet.from_subnet_attributes(self, "subnetid2", availability_zone="ap-southeast-2b", subnet_id=core.Fn.import_value("ApplicationSubnetAzB"))
        subnetid3=_ec2.Subnet.from_subnet_attributes(self, "subnetid3", availability_zone="ap-southeast-2c", subnet_id=core.Fn.import_value("ApplicationSubnetAzC"))
        vpc_subnets_selection = _ec2.SubnetSelection(subnets = [subnetid1, subnetid2, subnetid3])


        core.CfnOutput(self,
                       "customVpcOutput",
                       value=vpc.vpc_id,
                       description="VPC ID",
                       export_name=core.Fn.sub("PostgresVpcID-${AWS::StackName}")
                       )

        # Creating a subnet group for RDS instance            
        sub_group=_rds.CfnDBSubnetGroup(self,"postgressubnet",
                                        db_subnet_group_description=core.Fn.sub("postgresdbsubnetgroup-${AWS::StackName}"),
                                        db_subnet_group_name=core.Fn.sub("postgresdbsubnetgroup-${AWS::StackName}"),
                                        subnet_ids=[subnetid1.subnet_id, subnetid2.subnet_id]           
        )


        # Security group 
        postgres_rds_security_group = _ec2.SecurityGroup(self, "postgresSGID", 
                                                         vpc=vpc, 
                                                         security_group_name=core.Fn.sub("Postgres-RDS_Sec_Group-${AWS::StackName}")
                                                         )

        rds_ports = [5432]
        for port in rds_ports:
            ips = ["x.x.x.x/x","x.x.x.x/x"]
            for cidr in ips:
                postgres_rds_security_group.add_ingress_rule(peer=_ec2.Peer.ipv4(cidr), connection=_ec2.Port.tcp(port))

        core.CfnOutput(self,
                       "SecurityGroupID",
                       value=postgres_rds_security_group.security_group_id,
                       description="Security Group ID",
                       export_name=core.Fn.sub("PostgresSGId-${AWS::StackName}")
                      )

        # Mapping
        instance_class_map=core.CfnMapping(self,"InstSize",
                                           mapping={
                                               "instsize": {
                                                   "Small": "db.t3.small",
                                                   "Medium": "db.t3.medium",
                                                   "Large": "db.t3.large"
                                               }
                                           }   
                                           )

        db_instance_class = core.CfnParameter(self, "db_instance_class", type="String",
                                              description="Small = 1 VCPU + 2GB | Medium = 1 VPCU + 4GB | Large = 2VPCU + 8GB.",
                                              default="Small",
                                              allowed_values=["Small","Medium","Large"]
                                              )

        allocated_storage = core.CfnParameter(self, "allocated_storage", type="String",
                                              description="Please enter the storage size.",
                                              default="30",
                                              allowed_values=["30","40","50","60"]
                                              )

        master_username = core.CfnParameter(self, "master_username", type="String",
                                            description="Please enter the username. Default username is xxxxx.", 
                                            default="xxxxx"
                                            )

        master_user_password = core.CfnParameter(self, "master_user_password", type="String",
                                                 description="Please enter the password.",
                                                 no_echo=True)


        db_instance_identifier = core.CfnParameter(self, "db_instance_identifier", type="String",
                                                   description="Please enter the name for the DB instance. DB instance name can include numbers, lowercase letters, uppercase letters, hyphens (-), and forward slash (/).",
                                                   allowed_pattern= "^[0-9a-zA-Z-/]*$",
                                                   constraint_description= "DB instanceidentifier can include numbers, lowercase letters, uppercase letters, hyphens (-), and forward slash (/)."
                                                   )

        db_name = core.CfnParameter(self, "db_name", type="String",
                                    description="Please enter the DB name.",
                                    default="postgresdb"
                                    )
        
        multi_az = core.CfnParameter(self, "multi_az", type="String",
                                     description="Please enable or disable multiple Availability Zone deployment.", 
                                     default="False", 
                                     allowed_values=["True", "False"]
                                     )

        srg_function = core.CfnParameter(
            self, "TagFunction", 
            type="String",
            default="Storage",
            description="What function will this Database instance have?", 
        )

                            
        srg_cost_centre = core.CfnParameter(
            self, 
            "TagCostCentre", 
            type="String",
            description="Please select select cost code", 
            default="G151-xxxxxx", 
            allowed_values=[
            "G110-xxxxxx",
            "G111-xxxxxx",
            "G120-xxxxxx",
            "G121-xxxxxx",
            "G130-xxxxxx",
            "G131-xxxxxx",
            "G141-xxxxxx",
            "G150-xxxxxx",
            "G151-xxxxxx",
            "G160-xxxxxx",
            "G161-xxxxxx",
            "G171-xxxxxx",
            "G191-xxxxxx",
            "G201-xxxxxx",
            "G202-xxxxxx",
            "G220-xxxxxx"]
        )

        srg_environment = core.CfnParameter(
            self, 
            "TagEnvironment", 
            type="String",
            description="Please select environment type", 
            default="DEV", 
            allowed_values=["SBX","DEV","TST", "STG", "PRD"]
        )

        srg_owner = core.CfnParameter(
            self, 
            "TagOwner", 
            type="String",
            description="Please specify email of the team that will own the Database instance", 
            default="REPLACE.ME@superretailgroup.com",
            allowed_pattern="[\\p{Alpha}\\p{Digit}.]*@superretailgroup.com"
        )

        srg_managed_by = core.CfnParameter(
            self, 
            "TagManagedBy", 
            type="String",
            description="Please specify email of the team that will manage the Database instance", 
            default="REPLACE.ME@superretailgroup.com",
            allowed_pattern="[\\p{Alpha}\\p{Digit}.]*@superretailgroup.com|srgsrq@blazeclan.com|srgoperate@lemongrassconsulting.com|[\\p{Alpha}\\p{Digit}.]*@voicefoundry.com.au"
        )
                                       

        # Creating a new RDS instance
        postgres_rds_db = _rds.CfnDBInstance(self,"DBInstance",
                                #db_instance_class=db_instance_class.value_as_string, # db.t2.micro doesn't support encryption
                                db_instance_class=instance_class_map.find_in_map("instsize", db_instance_class.value_as_string),
                                engine="postgres",
                                engine_version="13.1", # Some versions don't support all logs specified in parameter for cloudwatch logs exports
                                allocated_storage=allocated_storage.value_as_string,
                                storage_encrypted=True,
                                master_username=master_username.value_as_string,
                                master_user_password=master_user_password.value_as_string,
                                backup_retention_period=7,
                                db_instance_identifier=db_instance_identifier.value_as_string,
                                db_name = db_name.value_as_string,
                                deletion_protection=False,
                                delete_automated_backups=True,
                                multi_az= multi_az.value,
                                # db_subnet_group_name=sub_group.db_subnet_group_name,
                                db_subnet_group_name=core.Fn.sub("postgresdbsubnetgroup-${AWS::StackName}"),
                                vpc_security_groups=[postgres_rds_security_group.security_group_id],
                                enable_cloudwatch_logs_exports=["postgresql","upgrade"],
                                #iops=1000 cannot be specified if io1 is not configured as storage_type. Condition??? 
                                storage_type="gp2"                              
                                )

        postgres_rds_db.apply_removal_policy(core.RemovalPolicy.DESTROY) # This is to apply DESTROY deletion policy so ther is no final snapshot. By default the final snapshot would be created on termination.
        
        # Cost centre tag format must be like GXXX, e.g. G191. 
        # Split away the label and keep the 4-character code.
        extracted_cost_code = core.Fn.select(
            0, core.Fn.split("-", srg_cost_centre.value_as_string) 
        )

        rds_tags = {'srg:function': srg_function.value_as_string, 'srg:cost-centre': extracted_cost_code, 'srg:environment': srg_environment.value_as_string, 'srg:owner': srg_owner.value_as_string, 'srg:managed-by': srg_managed_by.value_as_string}
        
        for key, value in rds_tags.items():
            core.Tag.add(postgres_rds_db,key, value)


        postgres_output = core.CfnOutput(self, "databaseNameOutput",
                                        description="Database name",
                                        value=postgres_rds_db.db_name,
                                        export_name=core.Fn.sub("Postgres-RDS-${AWS::StackName}")
                                        )

        rds_endpoint = core.CfnOutput(self, "RDSEndpointAddress",
                                        description= "postgres-rds-instance-endpoint-address",
                                        #value=f"mysql -h {mariadb_rds_db.attr_endpoint_address} -P 3306 -u admin -p",
                                        value=postgres_rds_db.attr_endpoint_address,
                                        export_name=core.Fn.sub("postgres-rds-instance-endpoint-address-${AWS::StackName}")
                                        )