!                           DARMA Toolkit v. 1.0.0
!
! Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC
! (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
! Government retains certain rights in this software.
!
! Redistribution and use in source and binary forms, with or without
! modification, are permitted provided that the following conditions are met:
!
! * Redistributions of source code must retain the above copyright notice,
!   this list of conditions and the following disclaimer.
!
! * Redistributions in binary form must reproduce the above copyright notice,
!   this list of conditions and the following disclaimer in the documentation
!   and/or other materials provided with the distribution.
!
! * Neither the name of the copyright holder nor the names of its
!   contributors may be used to endorse or promote products derived from this
!   software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
! AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
! IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
! ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
! LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
! CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
! SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
! INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
! CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
! ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
! POSSIBILITY OF SUCH DAMAGE.
!
! Questions? Contact darma@sandia.gov
!

program FWMP_constraints
  implicit none
  ! explicit integer declaration
  integer :: I, ii, jj
  integer :: K, kk, ll
  integer :: M, mm
  integer :: N, nn

  ! block-to-task assignment matrices
  logical, allocatable :: u_l(:,:)
  integer, allocatable :: u_i(:,:)

  ! block-to-rank assignment matrices
  logical, allocatable :: phi_l(:,:)
  integer, allocatable :: phi_i(:,:)

  ! task-to-rank assignment matrices
  logical, allocatable :: chi_l(:,:)
  logical, allocatable :: chi_t(:,:)
  integer, allocatable :: chi_i(:,:)

  ! comm-to-task assignment tensors
  logical, allocatable :: w_l(:,:,:)
  integer, allocatable :: w_i(:,:,:)

  ! comm-to-rank assignment tensors
  logical, allocatable :: psi_l(:,:,:)
  integer, allocatable :: psi_i(:,:,:)

  ! intermediate matrix
  logical, allocatable :: chi_w_l(:,:)

  ! tensor bounds
  integer, allocatable :: psi_lb_i(:,:,:)
  integer, allocatable :: psi_ub1_i(:,:,:)
  integer, allocatable :: psi_ub2_i(:,:,:)

  ! sums in paper formulas
  integer :: matrix_prod, matrix_sum, tensor_prod, tensor_sums(4)

  ! constraint checks
  integer :: n_checks, n_errors
  logical :: check_constraints

  print *
  print *, "### Full Work Model Problem Example"
  print *

  ! read and populate block-task assignments
  u_l = read_logical_matrix("u.txt")
  K = size(u_l, dim = 1)
  N = size(u_l, dim = 2)
  allocate(u_i(K, N))
  u_i = merge(1, 0, u_l)

  ! read and populate communication-task assignments
  w_l = read_logical_tensor("w.txt", K)
  M = size(w_l, dim = 3)
  allocate(w_i(K, K, M))
  w_i = merge(1, 0, w_l)

  ! read and populate task-rank assignments
  chi_l = read_logical_matrix("chi.txt")
  if (size(chi_l, dim = 2) /= K) then
       print *, "Inconsistent block-task-rank assignments, exiting. ###"
       stop 1, quiet=.TRUE.
    end if
  I = size(u_l, dim = 2)
  allocate(chi_t(I, K))
  chi_t = transpose(chi_l)
  allocate(chi_i(I, K))
  chi_i = merge(1, 0, chi_l)

  ! allocate derived assignments
  allocate(phi_l(I, N))
  allocate(phi_i(I, N))
  allocate(chi_w_l(I, K))
  allocate(psi_l(I, I, M))
  allocate(psi_i(I, I, M))
  allocate(psi_lb_i(I, I, M))
  allocate(psi_ub1_i(I, I, M))
  allocate(psi_ub2_i(I, I, M))

  ! print parameters
  print *, "## Parameters:"
  print *, "I = ", int_to_str(I)
  print *, "K = ", int_to_str(K)
  print *, "M = ", int_to_str(M)
  print *, "N = ", int_to_str(N)
  print *
  call print_logical_matrix("u", u_l)
  call print_integer_matrix("u", u_i)
  print *
  do mm = 1, M
     call print_logical_matrix("w::"//trim(int_to_str(mm)), w_l(:,:,mm))
  end do
  do mm = 1, M
     call print_integer_matrix("w::"//trim(int_to_str(mm)), w_i(:,:,mm))
  end do
  print *

  ! populate and print variables
  print *, "## Variables:"
  call print_logical_matrix("chi", chi_l)
  call print_integer_matrix("chi", chi_i)
  print *

  ! compute and print task-rank matrices
  phi_l = matmul(chi_l, u_l)
  phi_i = merge(1, 0, phi_l)
  call print_logical_matrix("phi", phi_l)
  call print_integer_matrix("phi", phi_i)
  print *

  ! generate integer block matrix relations
  print *, "# Integer block matrix relations:"
  print *, "-----------------------------------"
  print *, "i   n   k   u  chi  *  +  phi check"
  print *, "-----------------------------------"
  n_checks = 0
  n_errors = 0
  ! iterate over tensor slices
  do ii = 1, I
     ! iterate over from rank indices
     do nn = 1, N
        ! initialize sum
        matrix_sum = 0

        ! iterate over to task indices
        do kk = 1, K
           ! update sum
           matrix_prod = u_i(kk,nn) * chi_i(ii,kk)
           matrix_sum = matrix_sum + matrix_prod

           ! check and print innermost loop results
           check_constraints = phi_i(ii,nn) >= matrix_prod
           n_checks = n_checks + 1
           if (.not. check_constraints) then
              n_errors = n_errors + 1
           endif
           print "(I2,I4,I4,I4,I4,I4,L12)", &
                & ii, nn, kk, u_i(kk,nn), chi_i(ii,kk), matrix_prod, &
                & check_constraints
        end do ! kk

        ! store and check results aggregated at i,n level
        check_constraints = phi_i(ii,nn) <= matrix_sum
        n_checks = n_checks + 1
        if (.not. check_constraints) then
           n_errors = n_errors + 1
        endif
        print "(I25, I4, L5)", matrix_sum, phi_i(ii,nn), &
             & check_constraints
     end do ! nn
  end do ! ii
  print *, "-----------------------------------"
  print *

  ! compute and print communication-rank tensors
  psi_i = merge(1, 0, psi_l)
  do mm = 1, M
     chi_w_l = matmul(chi_l, w_l(:,:,mm))
     psi_l(:,:,mm) = matmul(chi_w_l, chi_t)
     call print_logical_matrix("psi::"//trim(int_to_str(mm)), psi_l(:,:,mm))
  end do
  do mm = 1, M
     psi_i = merge(1, 0, psi_l)
     call print_integer_matrix("psi::"//trim(int_to_str(mm)), psi_i(:,:,mm))
  end do
  print *

  ! generate integer communication tensor constraints
  print *, "# Integer communication tensor constraints:"
  print *, "------------------------------------------------------------"
  print *, "m   j   i   l   k   w  chi chiT *   +  lb  psi ub1 ub2 check"
  print *, "------------------------------------------------------------"
  n_errors = 0
  ! iterate over tensor slices
  do mm = 1, M
     ! iterate over from rank indices
     do jj = 1, I
        ! iterate over to rank indices
        do ii = 1, I
           ! initialize sums
           tensor_sums = 0

           ! iterate over from task indices
           do ll = 1, K
              ! iterate over to task indices
              do kk = 1, K
                 ! update sums
                 tensor_prod = chi_i(ii,kk) * chi_i(jj,ll) * w_i(kk,ll,mm)
                 tensor_sums(1) = tensor_sums(1) + tensor_prod
                 tensor_sums(2) = tensor_sums(2) + chi_i(ii,kk) * w_i(kk,ll,mm)
                 tensor_sums(3) = tensor_sums(3) + chi_i(jj,ll) * w_i(kk,ll,mm)
                 tensor_sums(4) = tensor_sums(4) + (chi_i(ii,kk) + chi_i(jj,ll)) * w_i(kk,ll,mm)

                 ! print innermost loop results
                 print "(I2,I4,I4,I4,I4,I4,I4,I4,I4)", &
                      & mm, jj, ii, ll, kk, w_i(kk,ll,mm), chi_i(ii,kk), chi_i(jj,ll), &
                      & tensor_prod
              end do ! kk
           end do ! ll

           ! store and check  results aggregated at i,j,m level
           psi_ub1_i(ii,jj,mm) = tensor_sums(2)
           check_constraints = psi_i(ii,jj,mm) <= psi_ub1_i(ii,jj,mm)
           n_checks = n_checks + 1
           if (.not. check_constraints) then
              n_errors = n_errors + 1
           endif
           psi_ub2_i(ii,jj,mm) = tensor_sums(3)
           check_constraints = check_constraints .and. psi_i(ii,jj,mm) <= psi_ub1_i(ii,jj,mm)
           n_checks = n_checks + 1
           if (.not. check_constraints) then
              n_errors = n_errors + 1
           endif
           psi_lb_i(ii,jj,mm) = tensor_sums(4) - 1
           check_constraints = check_constraints .and. psi_lb_i(ii,jj,mm) <= psi_i(ii,jj,mm)
           n_checks = n_checks + 1
           if (.not. check_constraints) then
              n_errors = n_errors + 1
           endif
           print "(I38, I4, I4, I4, I4, L5)", tensor_sums(1), &
                & psi_lb_i(ii,jj,mm), psi_i(ii,jj,mm), &
                & psi_ub1_i(ii,jj,mm), psi_ub2_i(ii,jj,mm), &
                & check_constraints
        end do ! jj
     end do ! ii
     print *, "   -------------------------------------------------------"
  end do ! mm
  print *

  ! print tensor bounds
  do mm = 1, M
     call print_integer_matrix("psi_lb::"//trim(int_to_str(mm)), psi_lb_i(:,:,mm))
  end do
  print *
  do mm = 1, M
     call print_integer_matrix("psi_ub1::"//trim(int_to_str(mm)), psi_ub1_i(:,:,mm))
  end do
  print *
  do mm = 1, M
     call print_integer_matrix("psi_ub2::"//trim(int_to_str(mm)), psi_ub2_i(:,:,mm))
  end do
  print *
  print *, "# Verified ", trim(int_to_str(n_checks)), " integer constraints"
  print *

  ! terminate program
  deallocate(psi_ub2_i)
  deallocate(psi_ub1_i)
  deallocate(psi_lb_i)
  deallocate(psi_i)
  deallocate(psi_l)
  deallocate(chi_w_l)
  deallocate(w_i)
  deallocate(w_l)
  deallocate(chi_i)
  deallocate(chi_t)
  deallocate(chi_l)
  deallocate(phi_i)
  deallocate(phi_l)
  deallocate(u_i)
  deallocate(u_l)
  if (n_errors > 0) then
     print *, "Program found ", trim(int_to_str(n_errors)), " errors ###"
  else
     print *, "Program completed without errors ###"
  endif
  print *

contains
  ! read logical matrix from file
  function read_logical_matrix(str) result(mat)
    implicit none
    ! pure function with logical matrix output
    character(*), intent(in) :: str
    logical, allocatable :: mat(:,:)

    ! internal variables
    integer :: ios, n_true, n_rows, n_cols, i, j
    character(len=512) :: msg

    ! open read-only file if it exists
    open(unit=1, file=str, status="old", action="read", iostat=ios, iomsg=msg)
    if (ios /= 0) then
       print *, trim(msg)
       stop 1, quiet=.TRUE.
    end if

    ! count number of true entries then rewind
    n_true = -1
    do
       read(1, *, iostat=ios)
       if (ios /= 0) exit
       n_true = n_true + 1
    end do
    if (n_true < 1) then
       print *, "No assignments, exiting. ###"
       stop 1, quiet=.TRUE.
    end if
    rewind 1

    ! read and set matrix shape
    read(1, *) n_rows, n_cols
    allocate(mat(n_rows, n_cols))
    mat = .FALSE.

    ! read and assign true entries
    do
       read(1, *, iostat=ios) i, j
       if (ios /= 0) exit
       if (i > 0 .and. i <= n_rows .and. j > 0 .and. j <= n_cols) mat(i,j) = .TRUE.
    end do

    ! close file
    close(1)

  end function read_logical_matrix

  ! read logical tensor from file
  function read_logical_tensor(str, n_tasks) result(ten)
    implicit none
    ! pure function with logical tensor output
    character(*), intent(in) :: str
    integer, intent(in) :: n_tasks
    logical, allocatable :: ten(:,:,:)

    ! internal variables
    integer :: ios, n_slices, k, l, m
    character(len=512) :: msg

    ! open read-only file if it exists
    open(unit=1, file=str, status="old", action="read", iostat=ios, iomsg=msg)
    if (ios /= 0) then
       print *, trim(msg)
       stop 1, quiet=.TRUE.
    end if

    ! count number of slices then rewind
    n_slices = 0
    do
       read(1, *, iostat=ios)
       if (ios /= 0) exit
       n_slices = n_slices + 1
    end do
    if (n_slices < 1) then
       print *, "No slices, exiting. ###"
       stop 1, quiet=.TRUE.
    end if
    rewind 1

    ! set tensor shape
    allocate(ten(n_tasks, n_tasks, n_slices))
    ten = .FALSE.

    ! read and assign true entries, one per slices
    m = 0
    do
       read(1, *, iostat=ios) k, l
       if (ios /= 0) exit
       m = m + 1
       if (k > 0 .and. k <= n_slices .and. l > 0 .and. l <= n_slices) ten(k,l,m) = .TRUE.
    end do

    ! close file
    close(1)

  end function read_logical_tensor

  ! print logical matrix to console
  subroutine print_logical_matrix(str, mat)
    implicit none
    ! read-only input variables
    character(*), intent(in) :: str
    logical, intent(in) :: mat(:,:)

    ! iterate over matrix rows
    integer :: rr
    print *, "# Boolean ", str, " ="
    do rr = 1, size(mat, dim = 1)
       print *, mat(rr, 1:size(mat, dim = 2))
    end do

  end subroutine print_logical_matrix

  ! print integer matrix to console
  subroutine print_integer_matrix(str, mat)
    implicit none
    ! read-only input variables
    character(*), intent(in) :: str
    integer, intent(in) :: mat(:,:)

    ! iterate over matrix rows
    integer :: rr
    print *, "# Integer ", str, " ="
    do rr = 1, size(mat, dim = 1)
       print *, mat(rr, 1:size(mat, dim = 2))
    end do

  end subroutine print_integer_matrix

  ! convert integer to string
  function int_to_str(I) result(str)
    implicit none
    ! pure function with pointer output
    integer, intent(in) :: I
    character(32) :: str

    ! convert and adjust
    write (str, *) I
    str = adjustl(str)

  end function int_to_str

end program FWMP_constraints
