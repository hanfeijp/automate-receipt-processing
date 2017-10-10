using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace WebOCR.Models
{
    public class Product
    {
        public string Type { get; set; }
        public string BoundingBox { get; set; }
        public float TextAccuracy { get; set; }
        public string OCRText { get; set; }
        public float OCRAccuracy { get; set; }
        private int _x;
        private int _y;
        private int _x2;
        private int _y2;
        public int X() { return _x; }
        public int Y() { return _y; }
        public int X2() { return _x2; }
        public int Y2() { return _y2; }
        public void SetX(int value) { _x = value; }
        public void SetY(int value) { _y = value; }
        public void SetX2(int value) { _x2 = value; }
        public void SetY2(int value) { _y2 = value; }
    }
}