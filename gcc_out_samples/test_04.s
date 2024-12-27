	.build_version macos,  14, 0
	.text
	.globl _main
_main:
LFB0:
	pushq	%rbp
LCFI0:
	movq	%rsp, %rbp
LCFI1:
	movl	$0, -4(%rbp)
	movl	$0, -8(%rbp)
	movl	$42, -12(%rbp)
	movl	-12(%rbp), %eax
	movl	%eax, -8(%rbp)
	movl	-8(%rbp), %eax
	movl	%eax, -4(%rbp)
	movl	-4(%rbp), %eax
	cmpl	-8(%rbp), %eax
	je	L2
	movl	-8(%rbp), %eax
	cmpl	-12(%rbp), %eax
	je	L2
	movl	$1, %eax
	jmp	L3
L2:
	movl	-4(%rbp), %eax
	cmpl	-8(%rbp), %eax
	jne	L4
	movl	-4(%rbp), %eax
	cmpl	-12(%rbp), %eax
	je	L5
L4:
	movl	$1, %eax
	jmp	L3
L5:
	movl	$0, %eax
L3:
	popq	%rbp
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
