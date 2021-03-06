
/*******************************************************************************
 ** Utility functions
 *******************************************************************************/

#include <Python.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "visclibs/utilities.h"

#if PY_MAJOR_VERSION >= 3
    #define PyString_AsString PyUnicode_AsUTF8
#endif

/*******************************************************************************
 ** makes a species list in C from PyObject
 *******************************************************************************/
 char* specieListFromPyObject(PyObject *specieListPy)
 {
     char *specieList;
     Py_ssize_t nspec, j;
     
     
     nspec = PyList_Size(specieListPy);
     specieList = malloc(3 * nspec * sizeof(char));
     if (specieList == NULL)
     {
         PyErr_SetString(PyExc_MemoryError, "specieListFromPyObject: could not allocate specieList");
         return NULL;
     }
     for (j = 0; j < nspec; j++)
     {
         int j3 = 3 * j;
         char *tmpsym = PyString_AsString(PyList_GetItem(specieListPy, j));
         specieList[j3    ] = tmpsym[0];
         specieList[j3 + 1] = tmpsym[1];
         specieList[j3 + 2] = '\0';
     }
     
     return specieList;
 }

/*******************************************************************************
 ** returns specie index of given specie in the specie list
 *******************************************************************************/
int getSpecieIndex( int NSpecies, char* specie, char* specieList )
{
    int i, comp, specieIndex;
    
    /* initialise to something wrong */
    specieIndex = -99;
    
    /* find a match */
    for ( i=0; i<NSpecies; i++ )
    {
        comp = strcmp( &specie[0], &specieList[3*i] );
        if ( comp == 0 )
        {
            specieIndex = i;
            break;
        }
    }
    
    return specieIndex;
}


/*******************************************************************************
 * Find separation vector between two atoms
 *******************************************************************************/
void atomSeparationVector( double *vector3, double ax, double ay, double az, double bx, double by, double bz, double xdim, double ydim, double zdim, int pbcx, int pbcy, int pbcz )
{
    double dx, dy, dz;
    
    
    /* calculate separation */
    dx = bx - ax;
    dy = by - ay;
    dz = bz - az;
    
    /* handle PBCs here if required */
    if ( pbcx == 1 )
    {
        dx = dx - round( dx / xdim ) * xdim;
    }
    if ( pbcy == 1 )
    {
        dy = dy - round( dy / ydim ) * ydim;
    }
    if ( pbcz == 1 )
    {
        dz = dz - round( dz / zdim ) * zdim;
    }
    
    vector3[0] = dx;
    vector3[1] = dy;
    vector3[2] = dz;
}


/*******************************************************************************
 ** return atomic separation squared
 *******************************************************************************/
double atomicSeparation2(double ax, double ay, double az, double bx, double by, double bz, double xdim,
        double ydim, double zdim, int pbcx, int pbcy, int pbcz)
{
    double rx, ry, rz, r2;
    
    /* calculate differences */
    rx = ax - bx;
    ry = ay - by;
    rz = az - bz;
    
    /* handle PBCs here, if required */
    if (pbcx == 1) rx = rx - round(rx / xdim) * xdim;
    if (pbcy == 1) ry = ry - round(ry / ydim) * ydim;
    if (pbcz == 1) rz = rz - round(rz / zdim) * zdim;
    
    /* separation squared */
    r2 = rx * rx + ry * ry + rz * rz;
    
    return r2;
}


/*******************************************************************************
 ** return atomic separation squared, with check if PBCs were applied
 *******************************************************************************/
double atomicSeparation2PBCCheck( double ax, double ay, double az, 
                          double bx, double by, double bz, 
                          double xdim, double ydim, double zdim, 
                          int pbcx, int pbcy, int pbcz,
                          int *appliedPBCs )
{
    double rx, ry, rz, r2;
    double rxini, ryini, rzini;
    
    /* calculate separation */
    rxini = ax - bx;
    ryini = ay - by;
    rzini = az - bz;
    
    /* handle PBCs here if required */
    if ( pbcx == 1 )
    {
        rx = rxini - round( rxini / xdim ) * xdim;
    }
    else
    {
        rx = rxini;
    }
    
    if ( pbcy == 1 )
    {
        ry = ryini - round( ryini / ydim ) * ydim;
    }
    else
    {
        ry = ryini;
    }
    
    if ( pbcz == 1 )
    {
        rz = rzini - round( rzini / zdim ) * zdim;
    }
    else
    {
        rz = rzini;
    }
    
    if (rx != rxini)
    {
        appliedPBCs[0] = 1;
    }
    else
    {
        appliedPBCs[0] = 0;
    }
    
    if (ry != ryini)
    {
        appliedPBCs[1] = 1;
    }
    else
    {
        appliedPBCs[1] = 0;
    }
    
    if (rz != rzini)
    {
        appliedPBCs[2] = 1;
    }
    else
    {
        appliedPBCs[2] = 0;
    }
    
    /* separation squared */
    r2 = rx * rx + ry * ry + rz * rz;
    
    return r2;
}
