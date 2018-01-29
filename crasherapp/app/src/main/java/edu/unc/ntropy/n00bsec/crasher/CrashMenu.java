package edu.unc.ntropy.n00bsec.crasher;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.TextView;

public class CrashMenu extends AppCompatActivity {

	// Used to load the 'native-lib' library on application startup.
	static {
		System.loadLibrary("native-lib");
	}

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_crash_menu);

		// Example of a call to a native method
		TextView tv = (TextView) findViewById(R.id.sample_text);
		tv.setText(stringFromJNI());
	}

	public void crashNative(View v){
		Log.d("CRASHER", "Get ready to crash!");
		crash();
		Log.d("CRASHER", "Damnit.");
	}

	/**
	 * A native method that is implemented by the 'native-lib' native library,
	 * which is packaged with this application.
	 */
	public native String stringFromJNI();
	public native void crash();
}
