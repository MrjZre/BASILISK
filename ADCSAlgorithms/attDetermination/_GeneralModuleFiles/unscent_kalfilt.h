

#include "matrix_operations.h"

#ifndef _UNSCENT_KALFILT_H_
#define _UNSCENT_KALFILT_H_

class UnscentKalFilt 
{

   public:
     UnscentKalFilt();
     virtual ~UnscentKalFilt();

   // UKF parameters
   int NumStates;  // state length
   int CountHalfSPs;             // -- Number of sigma points over 2
   int NumObs;                   // -- Number of measurements this cycle
   double beta;
   double alpha;
   double kappa;
   double lambda;
   double gamma;

   MatrixOperations Wm;
   MatrixOperations Wc;
     
   double dt;                     // -- seconds since last data epoch 
   double TimeTag;                // s  Time tag for statecovar/etc
   MatrixOperations state;        // -- State estimate for time TimeTag
   MatrixOperations Sbar;         // -- Time updated covariance
   MatrixOperations Covar;        // -- covariance   

   MatrixOperations obs;          // -- pseudorange observations 
   MatrixOperations *YMeas;        // -- Measurement model data

   MatrixOperations *SP;          // --    sigma point matrix 

   MatrixOperations Qnoise;       // -- process noise matrix 
   MatrixOperations SQnoise;      // -- cholesky of Qnoise 

   MatrixOperations Q_obs;  // -- to put on diagonal of Q obs matrix 

     void UKFInit();
     virtual void StateProp(MatrixOperations &StateCurr)=0;
     void TimeUpdateFilter(double UpdateTime);
     void MeasurementUpdate();
     virtual void ComputeMeasModel() = 0;
     void CholDownDate(MatrixOperations &R, MatrixOperations &XVec);
     virtual MatrixOperations ComputeSPVector(
        MatrixOperations SPError,
        MatrixOperations StateIn);
     virtual MatrixOperations ComputeObsError(
        MatrixOperations SPError,
        MatrixOperations StateIn);
//   void chol_decomp(double *A, double *L, int m);
//   void chol_updt(double *Sout, double *S, int n, double sca, double *u, double updn);
//   void chol_dndt(double *S, double *x, int n);
//   void QR_decomp(double *A, double *Q, double *R, int m, int n);
//   void inv_L(double *L, double *invL, int m);
//   void inv_U(double *U, double *invU, int m);
//   void matrix_mult(double *C, double *A, double *B, int m, int p, int n);
//   void matrix_print(double *A, int i, int j);
//   void matrix_transpose(double *At, double *A, int i, int j);
//   void ukf_rkf45(double *Y, double *Yout, double xend, double tol, int neq);
//
//   void nav_alg(NAVOUT_GUIDIN *nav_out, GNC_WORKSPACE *nav_work);

};

#endif
