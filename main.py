import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, RoundedRectangle, Rectangle

DATA_FILE = "fatura_verileri.json"
APP_VERSION = "v1.1.2"

IKONLAR = {
    "Aidat": "🏢", "Elektrik": "⚡", "Su": "💧", "Doğalgaz": "🔥",
    "Türksat": "📡", "Vodafone 1": "📱", "Vodafone 2": "📲",
    "Okul Servis Ücreti": "🚌", "Okul Etüt Ücreti": "📚",
    "Kredi Kartı 1": "💳", "Kredi Kartı 2": "💳",
    "Mazot": "⛽", "Benzin": "⛽", "Pazar Alışverişi": "🧺",
    "Market Alışverişi": "🛒", "Diğer": "📄"
}

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"bakiye": 0.0, "aylar": {}}
    return {"bakiye": 0.0, "aylar": {}}

def verileri_kaydet(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def su_anki_ay_str():
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    simdi = datetime.now()
    return f"{aylar[simdi.month - 1]} {simdi.year}"

class SplashEkran(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50)
        resim = "logo.jpg" if os.path.exists("logo.jpg") else "logo.jpeg"
        if os.path.exists(resim):
            layout.add_widget(Image(source=resim))
        else:
            layout.add_widget(Label(text="G-RAYEN\nFINANCE PRO", font_size='40sp', halign='center', color=(0, 0.8, 1, 1)))
        layout.add_widget(Label(text=f"Sürüm {APP_VERSION}", font_size='14sp', size_hint_y=None, height=30, color=(0.5, 0.5, 0.5, 1)))
        self.add_widget(layout)

class FaturaSatiri(BoxLayout):
    def __init__(self, isim, veri, odeme_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 110
        self.padding = [15, 10]
        self.spacing = 15
        with self.canvas.before:
            Color(*((0.1, 0.4, 0.2, 1) if veri['odendi'] else (0.6, 0.1, 0.1, 1)))
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20,])
        self.bind(size=self._update_rect, pos=self._update_rect)
        ikon = IKONLAR.get(veri.get("kategori", "Diğer"), "📄")
        sol = BoxLayout(orientation='vertical', size_hint_x=0.55)
        sol.add_widget(Label(text=f"{ikon} {isim.upper()}", bold=True, font_size='16sp', halign='left'))
        alt_bilgi = f"Son Tarih: {veri['son_tarih']}"
        if veri['odendi']: alt_bilgi = f"✓ {veri.get('odeme_zamani', '')}"
        sol.add_widget(Label(text=alt_bilgi, font_size='11sp', color=(0.9, 0.9, 0.9, 0.7)))
        self.add_widget(sol)
        self.add_widget(Label(text=f"{veri['tutar']:.2f} TL", bold=True, size_hint_x=0.25))
        btn_yazi = "İPTAL" if veri['odendi'] else "ÖDE"
        btn = Button(text=btn_yazi, size_hint_x=0.20, background_normal='', background_color=(1,1,1,0.15), bold=True)
        btn.bind(on_press=lambda x: odeme_callback(isim))
        self.add_widget(btn)
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class AnaEkran(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ay_str = su_anki_ay_str()
        self.silinecekler = []
        self.checkbox_referanslari = []
        self.layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg)
        self.yenile()
        self.add_widget(self.layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def ay_degistir(self, yon):
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        m_ay, m_yil = self.ay_str.split()
        idx = aylar.index(m_ay); yil = int(m_yil)
        if yon == "ileri":
            idx += 1
            if idx > 11: idx = 0; yil += 1
        else:
            idx -= 1
            if idx < 0: idx = 11; yil -= 1
        self.ay_str = f"{aylar[idx]} {yil}"
        self.yenile()

    def yenile(self):
        self.layout.clear_widgets()
        self.data = verileri_yukle()
        if self.ay_str not in self.data["aylar"]: self.data["aylar"][self.ay_str] = {}
        
        ay_secici = BoxLayout(size_hint_y=None, height=50, spacing=20)
        b_geri = Button(text="<", size_hint_x=0.2, background_color=(0.2, 0.2, 0.2, 1))
        b_geri.bind(on_press=lambda x: self.ay_degistir("geri"))
        ay_etiket = Label(text=self.ay_str.upper(), bold=True, font_size='18sp')
        b_ileri = Button(text=">", size_hint_x=0.2, background_color=(0.2, 0.2, 0.2, 1))
        b_ileri.bind(on_press=lambda x: self.ay_degistir("ileri"))
        ay_secici.add_widget(b_geri); ay_secici.add_widget(ay_etiket); ay_secici.add_widget(b_ileri)
        self.layout.add_widget(ay_secici)

        dash = BoxLayout(orientation='vertical', size_hint_y=0.25, padding=15, spacing=10)
        with dash.canvas.before:
            Color(0.12, 0.12, 0.18, 1)
            self.dash_rect = RoundedRectangle(size=dash.size, pos=dash.pos, radius=[25,])
        dash.bind(size=self._update_dash, pos=self._update_dash)
        
        ust = BoxLayout(spacing=10)
        ust.add_widget(Label(text=f"KASA\n[b]{self.data['bakiye']:.2f} TL[/b]", markup=True, font_size='22sp'))
        m_btn = Button(text="MENÜ", size_hint_x=0.3, background_color=(0, 0.5, 1, 1), bold=True)
        m_btn.bind(on_press=self.ayarlar_ac)
        ust.add_widget(m_btn)
        
        alt = BoxLayout(spacing=10)
        alt.add_widget(Label(text=f"ÖDENEN\n[color=00ff00]{sum(f['tutar'] for f in self.data['aylar'][self.ay_str].values() if f['odendi']):.2f}[/color]", markup=True, font_size='15sp'))
        alt.add_widget(Label(text=f"BORÇ\n[color=ff4444]{sum(f['tutar'] for f in self.data['aylar'][self.ay_str].values() if not f['odendi']):.2f}[/color]", markup=True, font_size='15sp'))
        dash.add_widget(ust); dash.add_widget(alt)
        self.layout.add_widget(dash)

        scroll = ScrollView()
        liste = GridLayout(cols=1, size_hint_y=None, spacing=10)
        liste.bind(minimum_height=liste.setter('height'))
        for isim, veri in self.data["aylar"][self.ay_str].items():
            liste.add_widget(FaturaSatiri(isim, veri, self.fatura_durum_degistir))
        scroll.add_widget(liste)
        self.layout.add_widget(scroll)
        self.layout.add_widget(Label(text=f"G-RAYEN Finance {APP_VERSION}", font_size='10sp', size_hint_y=None, height=15, color=(0.4, 0.4, 0.4, 1)))

    def _update_dash(self, instance, value):
        self.dash_rect.pos = instance.pos
        self.dash_rect.size = instance.size

    def fatura_durum_degistir(self, isim):
        f = self.data["aylar"][self.ay_str][isim]
        if not f["odendi"]:
            f["odendi"] = True
            f["odeme_zamani"] = datetime.now().strftime("%d.%m %H:%M")
            self.data["bakiye"] -= f["tutar"]
        else:
            f["odendi"] = False
            self.data["bakiye"] += f["tutar"]
        verileri_kaydet(self.data); self.yenile()

    def ayarlar_ac(self, instance):
        ic = BoxLayout(orientation='vertical', spacing=10, padding=15)
        btns = [("FATURA EKLE", (0, 0.6, 0.3, 1), self.ekle_popup), 
                ("GELECEK AYA AKTAR", (0, 0.4, 0.7, 1), self.ayi_devret_popup), 
                ("FATURA SİL", (0.7, 0.1, 0.1, 1), self.silme_listesi_popup),
                ("BAKİYE GÜNCELLE", (0.2, 0.2, 0.2, 1), self.bakiye_popup),
                ("ANA EKRANA DÖN", (0.4, 0.4, 0.4, 1), lambda x: self.menu_pop.dismiss())]
        for t, c, f in btns:
            b = Button(text=t, background_color=c, bold=True, size_hint_y=None, height=60)
            b.bind(on_press=f); ic.add_widget(b)
        self.menu_pop = Popup(title="MENÜ", content=ic, size_hint=(0.85, 0.75)); self.menu_pop.open()

    def silme_listesi_popup(self, x):
        self.menu_pop.dismiss()
        self.silinecekler = []
        self.checkbox_referanslari = []
        ana = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # TÜMÜNÜ SEÇ/KALDIR BUTONU
        ust_butonlar = BoxLayout(size_hint_y=None, height=50)
        self.tumunu_sec_btn = Button(text="TÜMÜNÜ SEÇ", background_color=(0.2, 0.4, 0.6, 1), bold=True)
        self.tumunu_sec_btn.bind(on_press=self.tumunu_sec_kaldir)
        ust_butonlar.add_widget(self.tumunu_sec_btn)
        ana.add_widget(ust_butonlar)
        
        sc = ScrollView()
        ic = GridLayout(cols=1, spacing=2, size_hint_y=None)
        ic.bind(minimum_height=ic.setter('height'))
        
        for i, isim in enumerate(self.data["aylar"][self.ay_str].keys()):
            satir_rengi = (0.18, 0.18, 0.25, 1) if i % 2 == 0 else (0.1, 0.1, 0.15, 1)
            satir = BoxLayout(size_hint_y=None, height=60, padding=[10, 0])
            with satir.canvas.before:
                Color(*satir_rengi)
                satir.bg_rect = Rectangle(size=satir.size, pos=satir.pos)
            satir.bind(size=lambda inst, val: setattr(inst.bg_rect, 'size', val) or setattr(inst.bg_rect, 'pos', inst.pos))
            
            cb = CheckBox(size_hint_x=0.2)
            cb.bind(active=lambda cb, value, n=isim: self.silme_listesine_ekle(n, value))
            self.checkbox_referanslari.append(cb)
            
            lbl = Label(text=isim.upper(), halign='left', size_hint_x=0.8, bold=True)
            satir.add_widget(cb); satir.add_widget(lbl)
            ic.add_widget(satir)
        
        sc.add_widget(ic); ana.add_widget(sc)
        btn_sil = Button(text="SEÇİLENLERİ SİL", size_hint_y=None, height=60, background_color=(0.7, 0.1, 0.1, 1), bold=True)
        btn_sil.bind(on_press=self.silme_onay_popup)
        ana.add_widget(btn_sil)
        bk = Button(text="İPTAL", size_hint_y=None, height=50, background_color=(0.3, 0.3, 0.3, 1))
        bk.bind(on_press=lambda x: self.s_pop.dismiss()); ana.add_widget(bk)
        self.s_pop = Popup(title="FATURA SİLME", content=ana, size_hint=(0.9, 0.8)); self.s_pop.open()

    def tumunu_sec_kaldir(self, instance):
        # Eğer hiçbiri seçili değilse veya bazıları seçiliyse hepsini seç, hepsi seçiliyse hepsini kaldır
        mevcut_durum = all(cb.active for cb in self.checkbox_referanslari) if self.checkbox_referanslari else False
        yeni_durum = not mevcut_durum
        
        for cb in self.checkbox_referanslari:
            cb.active = yeni_durum
        
        instance.text = "SEÇİMİ KALDIR" if yeni_durum else "TÜMÜNÜ SEÇ"

    def silme_listesine_ekle(self, isim, secili):
        if secili: 
            if isim not in self.silinecekler: self.silinecekler.append(isim)
        else:
            if isim in self.silinecekler: self.silinecekler.remove(isim)
        
        # Buton metnini dinamik güncelle
        if hasattr(self, 'tumunu_sec_btn'):
            hepsi_secili = all(cb.active for cb in self.checkbox_referanslari)
            self.tumunu_sec_btn.text = "SEÇİMİ KALDIR" if hepsi_secili else "TÜMÜNÜ SEÇ"

    def silme_onay_popup(self, x):
        if not self.silinecekler: return
        ic = BoxLayout(orientation='vertical', padding=15, spacing=15)
        ic.add_widget(Label(text=f"{len(self.silinecekler)} fatura silinecek.\nEmin misiniz?", halign='center'))
        btns = BoxLayout(spacing=10, size_hint_y=None, height=60)
        evet = Button(text="EVET", background_color=(0.7, 0.1, 0.1, 1), bold=True)
        evet.bind(on_press=self.toplu_fatura_sil)
        hayir = Button(text="HAYIR", background_color=(0.3, 0.3, 0.3, 1))
        hayir.bind(on_press=lambda x: self.onay_pop.dismiss())
        btns.add_widget(evet); btns.add_widget(hayir); ic.add_widget(btns)
        self.onay_pop = Popup(title="ONAY", content=ic, size_hint=(0.8, 0.35)); self.onay_pop.open()

    def toplu_fatura_sil(self, x):
        for isim in self.silinecekler:
            if isim in self.data["aylar"][self.ay_str]: del self.data["aylar"][self.ay_str][isim]
        verileri_kaydet(self.data); self.onay_pop.dismiss(); self.s_pop.dismiss(); self.yenile()

    def ayi_devret_popup(self, x):
        self.menu_pop.dismiss()
        ic = BoxLayout(orientation='vertical', padding=15, spacing=15)
        ic.add_widget(Label(text="Faturalar 0 TL olarak aktarılacak.\nOnaylıyor musunuz?", halign='center'))
        btns = BoxLayout(spacing=10, size_hint_y=None, height=60)
        ok = Button(text="EVET, DEVRET", background_color=(0, 0.6, 0.3, 1))
        ok.bind(on_press=self.ayi_devret_islem)
        cl = Button(text="VAZGEÇ", background_color=(0.7, 0.1, 0.1, 1))
        cl.bind(on_press=lambda x: self.devret_pop.dismiss())
        btns.add_widget(ok); btns.add_widget(cl); ic.add_widget(btns)
        self.devret_pop = Popup(title="AYLIK DEVİR", content=ic, size_hint=(0.85, 0.4)); self.devret_pop.open()

    def ayi_devret_islem(self, x):
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        m_ay, m_yil = self.ay_str.split()
        idx = aylar.index(m_ay); yil = int(m_yil)
        idx += 1
        if idx > 11: idx = 0; yil += 1
        gelecek_ay_str = f"{aylar[idx]} {yil}"
        if gelecek_ay_str not in self.data["aylar"]: self.data["aylar"][gelecek_ay_str] = {}
        for isim, veri in self.data["aylar"][self.ay_str].items():
            self.data["aylar"][gelecek_ay_str][isim] = {
                "tutar": 0.0, "son_tarih": f"20.{idx+1}.{yil}",
                "kategori": veri["kategori"], "odendi": False, "odeme_zamani": ""
            }
        verileri_kaydet(self.data); self.devret_pop.dismiss(); self.yenile()
        Popup(title="Başarılı", content=Label(text=f"{gelecek_ay_str} ayına aktarıldı!"), size_hint=(0.7, 0.3)).open()

    def bakiye_popup(self, x):
        self.menu_pop.dismiss()
        ic = BoxLayout(orientation='vertical', padding=15, spacing=15)
        self.b_in = TextInput(text=str(self.data['bakiye']), multiline=False, font_size='24sp', halign='center')
        ic.add_widget(self.b_in)
        btns = BoxLayout(spacing=10, size_hint_y=None, height=60)
        ok = Button(text="KAYDET", background_color=(0, 0.6, 0.3, 1)); ok.bind(on_press=self.bakiye_kaydet)
        cl = Button(text="GERİ", background_color=(0.7, 0.1, 0.1, 1)); cl.bind(on_press=lambda x: self.b_pop.dismiss())
        btns.add_widget(ok); btns.add_widget(cl); ic.add_widget(btns)
        self.b_pop = Popup(title="BAKİYE GÜNCELLE", content=ic, size_hint=(0.8, 0.4)); self.b_pop.open()

    def bakiye_kaydet(self, x):
        try:
            self.data["bakiye"] = float(self.b_in.text.replace(',', '.')); verileri_kaydet(self.data); self.b_pop.dismiss(); self.yenile()
        except: pass

    def ekle_popup(self, x):
        self.menu_pop.dismiss()
        ic = GridLayout(cols=2, padding=15, spacing=10)
        ic.add_widget(Label(text="Fatura Adı:"))
        self.f_ad = TextInput(multiline=False)
        ic.add_widget(self.f_ad)
        ic.add_widget(Label(text="Tutar:"))
        self.f_tu = TextInput(multiline=False)
        ic.add_widget(self.f_tu)
        ic.add_widget(Label(text="Kategori:"))
        self.f_ka = Spinner(text="Diğer", values=list(IKONLAR.keys()))
        ic.add_widget(self.f_ka)
        ic.add_widget(Label(text="Son Tarih:"))
        self.f_ta = TextInput(text=datetime.now().strftime("%d.%m.%Y"), multiline=False)
        ic.add_widget(self.f_ta)
        btns = BoxLayout(spacing=10, size_hint_y=None, height=60)
        ok = Button(text="EKLE", background_color=(0, 0.6, 0.3, 1)); ok.bind(on_press=self.fatura_olustur)
        cl = Button(text="GERİ", background_color=(0.7, 0.1, 0.1, 1)); cl.bind(on_press=lambda x: self.e_pop.dismiss())
        btns.add_widget(ok); btns.add_widget(cl)
        ana = BoxLayout(orientation='vertical', padding=10, spacing=10); ana.add_widget(ic); ana.add_widget(btns)
        self.e_pop = Popup(title="YENİ FATURA", content=ana, size_hint=(0.9, 0.7)); self.e_pop.open()

    def fatura_olustur(self, x):
        if self.f_ad.text:
            try:
                self.data["aylar"][self.ay_str][self.f_ad.text] = {
                    "tutar": float(self.f_tu.text.replace(',', '.')), 
                    "son_tarih": self.f_ta.text, "kategori": self.f_ka.text, 
                    "odendi": False, "odeme_zamani": ""
                }
                verileri_kaydet(self.data); self.e_pop.dismiss(); self.yenile()
            except: pass

class FaturaApp(App):
    def build(self):
        self.title = "G-RAYEN Finance"
        self.sm = ScreenManager()
        self.sm.add_widget(SplashEkran(name='splash'))
        self.sm.add_widget(AnaEkran(name='ana'))
        Clock.schedule_once(lambda dt: setattr(self.sm, 'current', 'ana'), 3)
        return self.sm

if __name__ == '__main__':
    FaturaApp().run()