package local.oneconnect;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public class MainActivity extends Activity {
  public void onCreate(Bundle state) {
    super.onCreate(state);
    WebView.setWebContentsDebuggingEnabled(true);
    WebView view = new WebView(this);
    view.getSettings().setJavaScriptEnabled(true);
    view.getSettings().setDomStorageEnabled(true);
    view.setWebViewClient(new WebViewClient());
    setContentView(view);
    view.loadUrl("http://127.0.0.1:18749/game/game.html");
  }
}

