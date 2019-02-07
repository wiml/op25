/*
 *   Copyright (C) 2015,2016 by Jonathan Naylor G4KLX
 *
 *   Modifications of original code to work with OP25
 *   Copyright (C) 2019 by Graham J. Norbury
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the Free Software
 *   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

#ifndef	Hamming_H
#define	Hamming_H

#include <vector>

typedef std::vector<bool> bit_vector;

class CHamming {
public:
	//static void encode15113_1(bool* d);
	static int decode15113_1(bit_vector& d, int s);

	//static void encode15113_2(bool* d);
	static int decode15113_2(bit_vector& d, int s);

	//static void encode1393(bool* d);
	static int decode1393(bit_vector& d, int s);

	//static void encode1063(bool* d);
	static int decode1063(bit_vector& d, int s);

	//static void encode16114(bool* d);
	static int decode16114(bit_vector& d, int s);

	//static void encode17123(bool* d);
	static int decode17123(bit_vector& d, int s);
};

#endif