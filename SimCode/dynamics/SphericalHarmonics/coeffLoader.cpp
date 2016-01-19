//
//  coeffLoader.cpp
//  SphericalHarmonics
//
//  Created by Manuel Diaz Ramos on 12/19/15.
//  Copyright © 2015 Manuel Diaz Ramos. All rights reserved.
//

#include "coeffLoader.h"
#include <stdio.h>
#include <string>
// basic file operations
#include <iostream>
#include <fstream>


///-------------------------------coeffLoader--------------------------------///
coeffLoader::coeffLoader()
{
    this->_errorMessage = string("");
}

coeffLoader::~coeffLoader()
{
    this->_errorMessage = string("");
}

/*!
 @brief Use this method to get the last error message.
 @return A string with the message.
 */
string coeffLoader::getLastErrorMessage(void)
{
    return this->_errorMessage;
}

/*!
 @brief Transforms the exponent character from D to E. Some coefficient files use D instead of E.
 */
void coeffLoader::replaceExpDesignator(string& str)
{
    string::iterator cii;
    
    for (cii = str.begin(); cii < str.end(); cii++)
    {
        if (*cii == 'D')
            *cii = 'E';
    }
    
    return;
}

///----------------------------coeffLoaderTest-----------------------------///
coeffLoaderTest::coeffLoaderTest()
    : coeffLoader()
{
    
}

coeffLoaderTest::~coeffLoaderTest()
{
    
}

bool coeffLoaderTest::load(const string& filename, double** C_bar, double** S_bar, unsigned int* degree)
{
    *degree = 10;
    
    
    for (unsigned int l = 0; l <= *degree; l++)
    {
        for (unsigned int m = 0; m <= l; m++)
        {
            C_bar[l][m] = (2*(*degree) - l - m + 1)/(*degree);
            S_bar[l][m] = (2*(*degree) - l - m + 1)/(*degree);
        }
    }
    
    return true;    
}

///----------------------------coeffLoaderCSV------------------------------///
coeffLoaderCSV::coeffLoaderCSV(const unsigned char separation_char) :
    coeffLoader(),
    _separationChar(separation_char)
{
    
}

coeffLoaderCSV::~coeffLoaderCSV()
{
    
}

/*!
 @brief Loads the coefficients into the pre-allocated matrices C_bar and S_bar.
 @param[in] filename Name of the file (and route) to be processed.
 @param[out] C_bar Array where the C coefficients are to be loaded. The array must be pre-allocated.
 @param[out] S_bar Array where the S coefficients are to be loaded. The array must be pre-allocated.
 @param[in-out] max_degree It specifies the maximum degree to be loaded. If the maximum degree present in the file is smaller, max_degree is modified.
 */
bool coeffLoaderCSV::load(const string& filename, double** C_bar, double** S_bar, unsigned int* max_degree)
{
    ifstream f;
    string line;
    string::iterator cii;
    string::iterator initial;
    
    int param_nmber;
    unsigned int degree = 0;
    unsigned int order = 0;
    double C_lm = 0;
    double S_lm = 0;
    long index;
    string aux;
    string::size_type sz;     // alias of size_t
    
    f.open(filename, ifstream::in);
    if (f.fail())
    {
        this->_errorMessage = "ERROR: The file could not be open.";
        return false;
    }
    
    while (getline(f, line))
    {
        if (degree > *max_degree)
            break;
        
        initial = line.begin();
        
        this->replaceExpDesignator(line); // Replace D with E if necessary
        
        param_nmber = 0;
        
        cii = initial;
        while (cii != line.end())
        {
            if (*cii == this->_separationChar)
            {
                cii++;
                continue;
            }
            
            if (param_nmber == 0)       // Degree
            {
                index = distance(initial, cii);
                aux = line.substr(index, string::npos);
                degree = (unsigned int) stod(aux, &sz);
                if (degree > *max_degree)
                    break;
                cii += sz;
                param_nmber++;
            }
            else if (param_nmber == 1)  // Order
            {
                index = distance(initial, cii);
                aux = line.substr(index, string::npos);
                order = stod(aux, &sz);
                cii += sz;
                param_nmber++;
            }
            else if (param_nmber == 2)  //C_bar
            {
                index = distance(initial, cii);
                aux = line.substr(index, string::npos);
                C_lm = stod(aux, &sz);
                cii += sz;
                param_nmber++;
            }
            else if (param_nmber == 3)  //S_bar
            {
                index = distance(initial, cii);
                aux = line.substr(index, string::npos);
                S_lm = stod(aux, &sz);
                cii += sz;
                param_nmber++;
            }
            else
            {
                C_bar[degree][order] = C_lm;
                S_bar[degree][order] = S_lm;
                
                break;
            }
        }
    }
    
    if (*max_degree > degree)
        *max_degree = degree;
    
    f.close();
    
    return true;
}