import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Drawer } from 'primeng/drawer';
import { Button } from 'primeng/button';
import { HistoryItem } from '../../models/media.model';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, Drawer, Button],
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss'
})
export class HistoryComponent {
  visible = input<boolean>(false);
  items = input<HistoryItem[]>([]);
  visibleChange = output<boolean>();
  selectItem = output<string>();
  clearHistory = output<void>();
}
