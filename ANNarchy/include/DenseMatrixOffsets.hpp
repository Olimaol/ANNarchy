/*
 *    DenseMatrixOffsets.hpp
 *
 *    This file is part of ANNarchy.
 *
 *    Copyright (C) 2021  Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>,
 *                        Julien Vitay <julien.vitay@gmail.com>
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    ANNarchy is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#pragma once

#include "DenseMatrix.hpp"

/*
 *  @brief              Connectivity representation using a full matrix.
 *  @tparam     IT      data type to represent the ranks within the matrix. Generally unsigned data types should be chosen.
 *                      The data type determines the maximum size for the number of elements in a column respectively the number
 *                      of rows encoded in the matrix:
 * 
 *                      - unsigned char (1 byte):        [0 .. 255]
 *                      - unsigned short int (2 byte):   [0 .. 65.535]
 *                      - unsigned int (4 byte):         [0 .. 4.294.967.295]
 *
 *                      The chosen data type should be able to represent the maximum values (LILMatrix::num_rows_ and ::num_columns_)
 * 
 *              ST      the second type should be used if the index type IT could overflow. For instance, the nb_synapses method should return ST as
 *                      the maximum value in case a full dense matrix would be IT times IT entries.
 *              MT      We need to store if a matrix value is set in a boolean mask. The size of each entry is determined by MT (we recommend char as its only 1 byte).
 */
template<typename IT = unsigned int, typename ST = unsigned long int, typename MT = char, bool row_major=true>
class DenseMatrixOffsets : public DenseMatrix<IT, ST, MT, row_major> {
protected:
    IT low_row_rank_;
    IT high_row_rank_;
    IT low_column_rank_;
    IT high_column_rank_;

    /*
     *  @brief      Decode the column indices for nonzeros in the matrix.
     */
    virtual std::vector<IT> decode_column_indices(IT row_idx) {
    #ifdef _DEBUG
        std::cout << "DenseMatrixOffsets::decode_column_indices()" << std::endl;
    #endif
        auto indices = std::vector<IT>();
        ST idx;
        if (row_major) {
            for (IT c = 0; c < this->num_columns_; c++) {
                idx = row_idx * this->num_columns_ + c;
                if (this->mask_[idx])
                    indices.push_back(c);
            }
        } else {
            for (IT c = 0; c < this->num_columns_; c++) {
                idx = c * this->num_rows_ + row_idx;
                if (this->mask_[idx])
                    indices.push_back(c);
            }
        }

        return indices;
    }

public:

    /**
     * @brief       Construct a new dense matrix object.
     * @details     This function does not allocate the matrix.
     *
     * @param[in]   num_rows      number of rows in the matrix
     * @param[in]   num_columns   number of columns in the matrix
     */
    explicit DenseMatrixOffsets(const IT low_row_rank, const IT high_row_rank, const IT low_column_rank, const IT high_column_rank):
        DenseMatrix<IT, ST, MT, row_major>(high_row_rank - low_row_rank, high_column_rank - low_column_rank) {
    #ifdef _DEBUG
        std::cout << "DenseMatrixOffsets::DenseMatrixOffsets()" << std::endl;
    #endif

        low_row_rank_ = low_row_rank;
        high_row_rank_ = high_row_rank;
        low_column_rank_ = low_column_rank;
        high_column_rank_ = high_column_rank;

        // we check if we can encode all possible values
        assert( (static_cast<long long>(this->num_rows_ * this->num_columns_) < static_cast<long long>(std::numeric_limits<ST>::max())) );
    }

    /**
     *  @brief      initialize connectivity based on a provided LIL representation.
     *  @details    simply sets the post_rank and pre_rank arrays without further sanity checking.
     */
    bool init_matrix_from_lil(std::vector<IT> &post_ranks, std::vector< std::vector<IT> > &pre_ranks) {
    #ifdef _DEBUG
        std::cout << "DenseMatrixOffsets::init_matrix_from_lil()" << std::endl;
    #endif
        // Sanity checks
        assert ( (post_ranks.size() == pre_ranks.size()) );
        assert ( (static_cast<unsigned long int>(post_ranks.size()) <= static_cast<unsigned long int>(std::numeric_limits<IT>::max())) );

        // Sanity check: enough memory?
        if (!this->check_free_memory(this->num_columns_ * this->num_rows_ * sizeof(MT)))
            return false;

        // Allocate mask
        this->mask_ = std::vector<MT>(this->num_rows_ * this->num_columns_, static_cast<MT>(false));

        // Iterate over LIL and update mask entries to *true* if nonzeros are existing.
        for (auto row_it = post_ranks.begin(); row_it != post_ranks.end(); row_it++) {
            IT row_idx = (*row_it) - low_row_rank_;

            for(auto inner_col_it = pre_ranks[row_idx].cbegin(); inner_col_it != pre_ranks[row_idx].cend(); inner_col_it++) {
                IT col_idx = (*inner_col_it) - low_column_rank_;
                if (row_major)
                    this->mask_[row_idx * this->num_columns_ + col_idx] = static_cast<MT>(true);
                else
                    this->mask_[col_idx * this->num_rows_ + row_idx] = static_cast<MT>(true);
            }
        }

        return true;
    }

    /**
     *  @brief      get a list of pre-synaptic neuron ranks and their efferent connections.
     *  @details    while the LILMatrix::nb_synapses and LILMatrix::nb_synapses_per_dendrite are row-centered this
     *              function contains the number of row entries for all columns with at least one row entry.
     *  @returns    a std::map with the pre-synaptic ranks as index and the number of nonzeros per column.
     */
    std::map<IT, IT> nb_efferent_synapses() {
        auto num_efferents = std::map<IT, IT>();

        if (row_major) {
            for (IT i = 0; i < this->num_rows_; i++) {
                for (IT j = 0; j < this->num_columns_; j++) {
                    ST idx = i*this->num_columns_ + j;
                    if (this->mask_[idx]) num_efferents[j+this->low_column_rank_]++;
                }
            }
        } else {
            for(IT j = 0; j < this->num_columns_; j++) {
                for(IT i = 0; i < this->num_rows_; i++) {
                    ST idx = j*this->num_rows_ + i;
                    if (this->mask_[idx]) num_efferents[j+this->low_column_rank_]++;
                }
            }
        }

        return num_efferents;
    }
};
