
/*******************************************************************************
 ** Copyright Chris Scott 2014
 ** IO routines written in C to improve performance
 *******************************************************************************/

#include <Python.h> // includes stdio.h, string.h, errno.h, stdlib.h
#include <numpy/arrayobject.h>
#include <math.h>
#include "array_utils.h"


static PyObject* readLatticeLBOMD(PyObject*, PyObject*);
static PyObject* readRef(PyObject*, PyObject*);
static PyObject* readLBOMDXYZ(PyObject*, PyObject*);
static int specieIndex(char*, int, char*);


/*******************************************************************************
 ** List of python methods available in this module
 *******************************************************************************/
static struct PyMethodDef methods[] = {
    {"readLatticeLBOMD", readLatticeLBOMD, METH_VARARGS, "Read LBOMD lattice format file"},
    {"readRef", readRef, METH_VARARGS, "Read LBOMD animation reference format file"},
    {"readLBOMDXYZ", readLBOMDXYZ, METH_VARARGS, "Read LBOMD XYZ format file"},
    {NULL, NULL, 0, NULL}
};

/*******************************************************************************
 ** Module initialisation function
 *******************************************************************************/
PyMODINIT_FUNC
init_input(void)
{
    (void)Py_InitModule("_input", methods);
    import_array();
}

/*******************************************************************************
 * Update specie list and counter
 *******************************************************************************/
static int specieIndex(char* sym, int NSpecies, char* specieList)
{
    int index, j, comp;
    
    
    index = NSpecies;
    for (j=0; j<NSpecies; j++)
    {
        comp = strcmp( &specieList[3*j], &sym[0] );
        if (comp == 0)
        {
            index = j;
            
            break;
        }
    }
    
    return index;
}


/*******************************************************************************
** read animation-reference file
*******************************************************************************/
static PyObject*
readRef(PyObject *self, PyObject *args)
{
	char *file, *specieList_c;
	int *atomID, *specie, *specieCount_c;
	double *pos, *charge, *maxPos, *minPos, *KE, *PE, *force;
	PyArrayObject *atomIDIn=NULL;
	PyArrayObject *specieIn=NULL;
	PyArrayObject *posIn=NULL;
	PyArrayObject *chargeIn=NULL;
	PyArrayObject *specieList_cIn=NULL;
	PyArrayObject *specieCount_cIn=NULL;
	PyArrayObject *maxPosIn=NULL;
	PyArrayObject *minPosIn=NULL;
	PyArrayObject *KEIn=NULL;
	PyArrayObject *PEIn=NULL;
	PyArrayObject *forceIn=NULL;
	
    int i, NAtoms, specInd, stat;
    FILE *INFILE;
    double xdim, ydim, zdim;
    char symtemp[3];
    char* specieList;
    double xpos, ypos, zpos;
    double xforce, yforce, zforce;
    int id, index, NSpecies;
    double ketemp, petemp, chargetemp;
    
    /* parse and check arguments from Python */
	if (!PyArg_ParseTuple(args, "sO!O!O!O!O!O!O!O!O!O!O!", &file, &PyArray_Type, &atomIDIn, &PyArray_Type, &specieIn, 
			&PyArray_Type, &posIn, &PyArray_Type, &chargeIn, &PyArray_Type, &KEIn, &PyArray_Type, &PEIn, 
			&PyArray_Type, &forceIn, &PyArray_Type, &specieList_cIn, &PyArray_Type, 
			&specieCount_cIn, &PyArray_Type, &maxPosIn, &PyArray_Type, &minPosIn))
		return NULL;
	
	if (not_intVector(atomIDIn)) return NULL;
	atomID = pyvector_to_Cptr_int(atomIDIn);
	
	if (not_doubleVector(posIn)) return NULL;
	pos = pyvector_to_Cptr_double(posIn);
	
	if (not_doubleVector(chargeIn)) return NULL;
	charge = pyvector_to_Cptr_double(chargeIn);
	
	if (not_doubleVector(KEIn)) return NULL;
	KE = pyvector_to_Cptr_double(KEIn);
	
	if (not_doubleVector(PEIn)) return NULL;
	PE = pyvector_to_Cptr_double(PEIn);
	
	if (not_doubleVector(forceIn)) return NULL;
	force = pyvector_to_Cptr_double(forceIn);
	
	if (not_doubleVector(minPosIn)) return NULL;
	minPos = pyvector_to_Cptr_double(minPosIn);
	
	if (not_doubleVector(maxPosIn)) return NULL;
	maxPos = pyvector_to_Cptr_double(maxPosIn);
	
	if (not_intVector(specieCount_cIn)) return NULL;
	specieCount_c = pyvector_to_Cptr_int(specieCount_cIn);
	
	if (not_intVector(specieIn)) return NULL;
	specie = pyvector_to_Cptr_int(specieIn);
	
	// no test yet for nx2 char*
	specieList_c = pyvector_to_Cptr_char(specieList_cIn);
    
	/* open file */
    INFILE = fopen( file, "r" );
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    stat = fscanf(INFILE, "%d", &NAtoms);
    if (stat != 1) return Py_BuildValue("i", -3);
    
    stat = fscanf(INFILE, "%lf%lf%lf", &xdim, &ydim, &zdim);
    if (stat != 3) return Py_BuildValue("i", -3);
    
    specieList = malloc(3 * sizeof(char));
    
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    NSpecies = 0;
    for (i=0; i<NAtoms; i++)
    {
        stat = fscanf(INFILE, "%d%s%lf%lf%lf%lf%lf%lf%lf%lf%lf", &id, symtemp, &xpos, &ypos, &zpos, &ketemp, &petemp, &xforce, &yforce, &zforce, &chargetemp);
        if (stat != 11) return Py_BuildValue("i", -3);
        
        /* index for storage is (id-1) */
        index = id - 1;
        
        atomID[index] = id;
        
        pos[3*index] = xpos;
        pos[3*index+1] = ypos;
        pos[3*index+2] = zpos;
        
        KE[index] = ketemp;
        PE[index] = petemp;
        
//        force[3*index] = xforce;
//        force[3*index+1] = yforce;
//        force[3*index+2] = zforce;
        
        charge[index] = chargetemp;
        
        /* find specie index */
        specInd = specieIndex(symtemp, NSpecies, specieList);
        
        specie[i] = specInd;
        
        if (specInd == NSpecies)
        {
            /* new specie */
            specieList = realloc( specieList, 3 * (NSpecies+1) * sizeof(char) );
            
            specieList[3*specInd] = symtemp[0];
            specieList[3*specInd+1] = symtemp[1];
            specieList[3*specInd+2] = symtemp[2];
            
            specieList_c[2*specInd] = symtemp[0];
            specieList_c[2*specInd+1] = symtemp[1];
            
            NSpecies++;
        }
        
        /* update specie counter */
        specieCount_c[specInd]++;
                
        /* max and min positions */
        if ( xpos > maxPos[0] ) maxPos[0] = xpos;
        if ( ypos > maxPos[1] ) maxPos[1] = ypos;
        if ( zpos > maxPos[2] ) maxPos[2] = zpos;
        if ( xpos < minPos[0] ) minPos[0] = xpos;
        if ( ypos < minPos[1] ) minPos[1] = ypos;
        if ( zpos < minPos[2] ) minPos[2] = zpos;
    }
    
    fclose(INFILE);
    
    /* terminate specie list */
    specieList_c[2*NSpecies] = 'X';
    specieList_c[2*NSpecies+1] = 'X';
    
    free(specieList);
    
    return Py_BuildValue("i", 0);
}


/*******************************************************************************
** read xyz input file
*******************************************************************************/
static PyObject*
readLBOMDXYZ(PyObject *self, PyObject *args)
{
	char *file;
	int *atomID, xyzformat;
	double *pos, *charge, *maxPos, *minPos, *KE, *PE, *force;
	PyArrayObject *atomIDIn=NULL;
	PyArrayObject *posIn=NULL;
	PyArrayObject *chargeIn=NULL;
	PyArrayObject *maxPosIn=NULL;
	PyArrayObject *minPosIn=NULL;
	PyArrayObject *KEIn=NULL;
	PyArrayObject *PEIn=NULL;
	PyArrayObject *forceIn=NULL;
	
    FILE *INFILE;
    int i, index, id, NAtoms, stat;
    double simTime, xpos, ypos, zpos;
    double chargetmp, KEtmp, PEtmp;
//    double xfor, yfor, zfor;
    
    /* parse and check arguments from Python */
	if (!PyArg_ParseTuple(args, "sO!O!O!O!O!O!O!O!i", &file, &PyArray_Type, &atomIDIn, &PyArray_Type, &posIn, 
			&PyArray_Type, &chargeIn, &PyArray_Type, &KEIn, &PyArray_Type, &PEIn, &PyArray_Type, &forceIn, 
			&PyArray_Type, &maxPosIn, &PyArray_Type, &minPosIn, &xyzformat))
		return NULL;
	
	if (not_intVector(atomIDIn)) return NULL;
	atomID = pyvector_to_Cptr_int(atomIDIn);
	
	if (not_doubleVector(posIn)) return NULL;
	pos = pyvector_to_Cptr_double(posIn);
	
	if (not_doubleVector(chargeIn)) return NULL;
	charge = pyvector_to_Cptr_double(chargeIn);
	
	if (not_doubleVector(KEIn)) return NULL;
	KE = pyvector_to_Cptr_double(KEIn);
	
	if (not_doubleVector(PEIn)) return NULL;
	PE = pyvector_to_Cptr_double(PEIn);
	
	if (not_doubleVector(forceIn)) return NULL;
	force = pyvector_to_Cptr_double(forceIn);
	
	if (not_doubleVector(minPosIn)) return NULL;
	minPos = pyvector_to_Cptr_double(minPosIn);
	
	if (not_doubleVector(maxPosIn)) return NULL;
	maxPos = pyvector_to_Cptr_double(maxPosIn);
    
    /* open file */
    INFILE = fopen(file, "r");
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    /* read header */
    stat = fscanf(INFILE, "%d", &NAtoms);
    if (stat != 1) return Py_BuildValue("i", -3);
    
    stat = fscanf(INFILE, "%lf", &simTime);
    if (stat != 1) return Py_BuildValue("i", -3);
        
    /* read atoms */
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    for (i=0; i<NAtoms; i++)
    {
        if (xyzformat == 0)
        {
            stat = fscanf(INFILE, "%d %lf %lf %lf %lf %lf", &id, &xpos, &ypos, &zpos, &KEtmp, &PEtmp);
            if (stat != 6) return Py_BuildValue("i", -3);
        }
        else if (xyzformat == 1)
        {
            stat = fscanf(INFILE, "%d%lf%lf%lf%lf%lf%lf", &id, &xpos, &ypos, &zpos, &KEtmp, &PEtmp, &chargetmp);
            if (stat != 7) return Py_BuildValue("i", -3);
        }
        
        index = id - 1;
        
        /* store data */
        atomID[index] = id;
        
        pos[3*index] = xpos;
        pos[3*index+1] = ypos;
        pos[3*index+2] = zpos;
        
        KE[index] = KEtmp;
        PE[index] = PEtmp;
        
        if (xyzformat == 1) charge[index] = chargetmp;
        
        /* max and min positions */
        if ( xpos > maxPos[0] ) maxPos[0] = xpos;
        if ( ypos > maxPos[1] ) maxPos[1] = ypos;
        if ( zpos > maxPos[2] ) maxPos[2] = zpos;
        if ( xpos < minPos[0] ) minPos[0] = xpos;
        if ( ypos < minPos[1] ) minPos[1] = ypos;
        if ( zpos < minPos[2] ) minPos[2] = zpos;
    }
    
    fclose(INFILE);
    
    return Py_BuildValue("i", 0);
}


/*******************************************************************************
 * Read LBOMD lattice file
 *******************************************************************************/
static PyObject*
readLatticeLBOMD(PyObject *self, PyObject *args)
{
    char *file, *specieList_c;
    int *atomID, *specie, *specieCount_c;
    double *pos, *charge, *maxPos, *minPos;
    PyArrayObject *atomIDIn=NULL;
    PyArrayObject *specieIn=NULL;
    PyArrayObject *posIn=NULL;
    PyArrayObject *chargeIn=NULL;
    PyArrayObject *specieList_cIn=NULL;
    PyArrayObject *specieCount_cIn=NULL;
    PyArrayObject *maxPosIn=NULL;
    PyArrayObject *minPosIn=NULL;
    
    FILE *INFILE;
    int i, NAtoms, specInd;
    double xdim, ydim, zdim;
    char symtemp[3];
    char* specieList;
    double xpos, ypos, zpos, chargetemp;
    int NSpecies, stat;
    
    
    /* parse and check arguments from Python */
    if (!PyArg_ParseTuple(args, "sO!O!O!O!O!O!O!O!", &file, &PyArray_Type, &atomIDIn, &PyArray_Type, &specieIn, 
            &PyArray_Type, &posIn, &PyArray_Type, &chargeIn, &PyArray_Type, &specieList_cIn, &PyArray_Type, 
            &specieCount_cIn, &PyArray_Type, &maxPosIn, &PyArray_Type, &minPosIn))
        return NULL;
    
    if (not_intVector(atomIDIn)) return NULL;
    atomID = pyvector_to_Cptr_int(atomIDIn);
    
    if (not_doubleVector(posIn)) return NULL;
    pos = pyvector_to_Cptr_double(posIn);
    
    if (not_doubleVector(chargeIn)) return NULL;
    charge = pyvector_to_Cptr_double(chargeIn);
    
    if (not_doubleVector(minPosIn)) return NULL;
    minPos = pyvector_to_Cptr_double(minPosIn);
    
    if (not_doubleVector(maxPosIn)) return NULL;
    maxPos = pyvector_to_Cptr_double(maxPosIn);
    
    if (not_intVector(specieCount_cIn)) return NULL;
    specieCount_c = pyvector_to_Cptr_int(specieCount_cIn);
    
    if (not_intVector(specieIn)) return NULL;
    specie = pyvector_to_Cptr_int(specieIn);
    
    // no test yet for nx2 char*
    specieList_c = pyvector_to_Cptr_char(specieList_cIn);
    
    /* open file */
    INFILE = fopen( file, "r" );
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    /* read header */
    stat = fscanf( INFILE, "%d", &NAtoms );
    if (stat != 1)
        return Py_BuildValue("i", -3);
    
    stat = fscanf(INFILE, "%lf %lf %lf", &xdim, &ydim, &zdim);
    if (stat != 3)
        return Py_BuildValue("i", -3);
    
    /* allocate specieList */
    specieList = malloc( 3 * sizeof(char) );
    
    /* read in atoms */
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    NSpecies = 0;
    for (i=0; i<NAtoms; i++)
    {
        stat = fscanf(INFILE, "%s %lf %lf %lf %lf", symtemp, &xpos, &ypos, &zpos, &chargetemp);
        if (stat != 5)
            return Py_BuildValue("i", -3);
        
        /* atom ID */
        atomID[i] = i + 1;
        
        /* store position and charge */
        pos[3*i] = xpos;
        pos[3*i+1] = ypos;
        pos[3*i+2] = zpos;
        
        charge[i] = chargetemp;
        
        /* find specie index */
        specInd = specieIndex(symtemp, NSpecies, specieList);
        
        specie[i] = specInd;
        
        if (specInd == NSpecies)
        {
            /* new specie */
            specieList = realloc( specieList, 3 * (NSpecies+1) * sizeof(char) );
            
            specieList[3*specInd] = symtemp[0];
            specieList[3*specInd+1] = symtemp[1];
            specieList[3*specInd+2] = symtemp[2];
            
            specieList_c[2*specInd] = symtemp[0];
            specieList_c[2*specInd+1] = symtemp[1];
            
            NSpecies++;
        }
        
        /* update specie counter */
        specieCount_c[specInd]++;
                
        /* max and min positions */
        if ( xpos > maxPos[0] ) maxPos[0] = xpos;
        if ( ypos > maxPos[1] ) maxPos[1] = ypos;
        if ( zpos > maxPos[2] ) maxPos[2] = zpos;
        if ( xpos < minPos[0] ) minPos[0] = xpos;
        if ( ypos < minPos[1] ) minPos[1] = ypos;
        if ( zpos < minPos[2] ) minPos[2] = zpos;
    }
    
    fclose(INFILE);
    
    /* terminate specie list */
    specieList_c[2*NSpecies] = 'X';
    specieList_c[2*NSpecies+1] = 'X';
        
    free(specieList);
    
    return Py_BuildValue("i", 0);
}
