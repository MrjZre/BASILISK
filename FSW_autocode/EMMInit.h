typedef struct {
	IMUConfigData imuSensorDecode;
	CSSConfigData cssSensorDecode;
	CSSWLSConfig CSSWlsEst;
	sunSafePointConfig sunSafePoint;
	simpleDeadbandConfig simpleDeadband;
	MRP_PDConfig MRP_PD;
	sunSafeACSConfig sunSafeACS;
	celestialBodyPointConfig sunPoint;
	celestialBodyPointConfig earthPoint;
	celestialBodyPointConfig marsPoint;
	attRefGenConfig attMnvrPoint;
	MRP_SteeringConfig MRP_SteeringRWA;
	dvAttEffectConfig RWAMappingData;
	rwNullSpaceConfig RWNullSpace;
	dvGuidanceConfig dvGuidance;
	MRP_SteeringConfig MRP_SteeringMOI;
	dvAttEffectConfig dvAttEffect;
	thrustRWDesatConfig thrustRWDesat;
	STConfigData stSensorDecode;
	inertial3DConfig inertial3D;
	hillPointConfig hillPoint;
	velocityPointConfig velocityPoint;
	celestialTwoBodyPointConfig celTwoBodyPoint;
	rasterManagerConfig rasterManager;
	eulerRotationConfig eulerRotation;
	inertial3DSpinConfig inertial3DSpin;
	attTrackingErrorConfig attTrackingError;
	errorDeadbandConfig errorDeadband;
	MRP_FeedbackConfig MRP_FeedbackRWA;
	PRV_SteeringConfig PRV_SteeringRWA;
}EMMConfigData;