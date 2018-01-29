#include <jni.h>
#include <string>

extern "C"
JNIEXPORT jstring

JNICALL
Java_edu_unc_ntropy_n00bsec_crasher_CrashMenu_stringFromJNI(
        JNIEnv *env,
        jobject /* this */) {
    std::string hello = "Hello from C++";
    return env->NewStringUTF(hello.c_str());
}

extern "C"
JNIEXPORT void
JNICALL
Java_edu_unc_ntropy_n00bsec_crasher_CrashMenu_crash(
        JNIEnv *env,
        jobject /* this */){
   *(int*)0x1bad1dea = 0;

}
