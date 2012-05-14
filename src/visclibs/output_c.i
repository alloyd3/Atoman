/* output_c.i */

/*******************************************************************************
 ** Copyright Chris Scott 2012
 ** SWIG interface file to io_module.c
 *******************************************************************************/

/* header */
%module output_c

%include carrays.i
%include typemaps.i
%include cstring.i

%{
#define SWIG_FILE_WITH_INIT
%}

/* required to pass numpy arrays */
%include "numpy.i"
%init %{
import_array();
%}

/* required to pass arrays of chars */
%numpy_typemaps(char, NPY_STRING, int)

/* define numpy arrays here */
/* 1d arrays of doubles */
%apply (int DIM1, double* INPLACE_ARRAY1) {
    (int posDim, double* pos),
    (int specieCovRadDim, double* specieCovRad)
}

/* 2d array of doubles */
%apply (int DIM1, int DIM2, double *INPLACE_ARRAY2) {
    (int specieRGBDim1, int specieRGBDim2, double *specieRGB)
}

/* 1d arrays of chars */
%apply (int DIM1, char* INPLACE_ARRAY1) {
    (int dim6, char* sym),
    (int speclistDim, char* specieList_c)
}

/* 1d arrays of ints */
%apply (int DIM1, int* INPLACE_ARRAY1) {
    (int specieDim, int* specie),
    (int visibleAtomsDim, int *visibleAtoms)
}

/* define functions here */
%{
extern void writePOVRAYAtoms(char *filename, int specieDim, int *specie, int posDim, double *pos, 
                             int visibleAtomsDim, int *visibleAtoms, int specieRGBDim1, int specieRGBDim2, 
                             double *specieRGB, int specieCovRadDim, double *specieCovRad);
%}

extern void writePOVRAYAtoms(char *filename, int specieDim, int *specie, int posDim, double *pos, 
                             int visibleAtomsDim, int *visibleAtoms, int specieRGBDim1, int specieRGBDim2, 
                             double *specieRGB, int specieCovRadDim, double *specieCovRad);
