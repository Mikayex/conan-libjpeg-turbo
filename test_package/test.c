#include <stdio.h>
#include "jpeglib.h"

int return_value = 1;

void JPEGVersionError(j_common_ptr cinfo)
{
    int jpeg_version = cinfo->err->msg_parm.i[0];
    printf("JPEG version: %d\n", jpeg_version);
    return_value = 0;
}

int main()
{
    struct jpeg_decompress_struct cinfo;
    struct jpeg_error_mgr error_mgr;
    error_mgr.error_exit = &JPEGVersionError;
    cinfo.err = &error_mgr;
    jpeg_CreateDecompress(&cinfo, -1 /*version*/, sizeof(struct jpeg_decompress_struct)); // Pass -1 to always force an error
    return return_value;
}