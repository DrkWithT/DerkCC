	.build_version macos,  14, 0
; GNU C99 (Homebrew GCC 14.2.0) version 14.2.0 (x86_64-apple-darwin23)
;	compiled by GNU C version 14.2.0, GMP version 6.3.0, MPFR version 4.2.1, MPC version 1.3.1, isl version isl-0.27-GMP

; GGC heuristics: --param ggc-min-expand=100 --param ggc-min-heapsize=131072
; options passed: -fPIC -mmacosx-version-min=14.0.0 -mtune=core2 -std=c99
	.text
	.globl _main
_main:
LFB0:
	pushq	%rbp	#
LCFI0:
	movq	%rsp, %rbp	#,
LCFI1:
; ../c_samples/test_04a.c:4:     int a = 1;
	movl	$1, -4(%rbp)	#, a
; ../c_samples/test_04a.c:5:     int b = 1;
	movl	$1, -8(%rbp)	#, b
; ../c_samples/test_04a.c:7:     if (a > 0 && b > 0) {
	cmpl	$0, -4(%rbp)	#, a
	jle	L2	#,
; ../c_samples/test_04a.c:7:     if (a > 0 && b > 0) {
	cmpl	$0, -8(%rbp)	#, b
	jle	L2	#,
; ../c_samples/test_04a.c:8:         return 0;
	movl	$0, %eax	#, _1
	jmp	L3	#
L2:
; ../c_samples/test_04a.c:11:     return 1;
	movl	$1, %eax	#, _1
L3:
; ../c_samples/test_04a.c:12: }
	popq	%rbp	#
LCFI2:
	ret	
LFE0:
	.section __TEXT,__eh_frame,coalesced,no_toc+strip_static_syms+live_support
EH_frame1:
	.set L$set$0,LECIE1-LSCIE1
	.long L$set$0
LSCIE1:
	.long	0
	.byte	0x3
	.ascii "zR\0"
	.uleb128 0x1
	.sleb128 -8
	.uleb128 0x10
	.uleb128 0x1
	.byte	0x10
	.byte	0xc
	.uleb128 0x7
	.uleb128 0x8
	.byte	0x90
	.uleb128 0x1
	.align 3
LECIE1:
LSFDE1:
	.set L$set$1,LEFDE1-LASFDE1
	.long L$set$1
LASFDE1:
	.long	LASFDE1-EH_frame1
	.quad	LFB0-.
	.set L$set$2,LFE0-LFB0
	.quad L$set$2
	.uleb128 0
	.byte	0x4
	.set L$set$3,LCFI0-LFB0
	.long L$set$3
	.byte	0xe
	.uleb128 0x10
	.byte	0x86
	.uleb128 0x2
	.byte	0x4
	.set L$set$4,LCFI1-LCFI0
	.long L$set$4
	.byte	0xd
	.uleb128 0x6
	.byte	0x4
	.set L$set$5,LCFI2-LCFI1
	.long L$set$5
	.byte	0xc
	.uleb128 0x7
	.uleb128 0x8
	.align 3
LEFDE1:
	.ident	"GCC: (Homebrew GCC 14.2.0) 14.2.0"
	.subsections_via_symbols
