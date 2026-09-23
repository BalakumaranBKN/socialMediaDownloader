import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Button } from 'primeng/button';
import { BadgeModule } from 'primeng/badge';
import { PlatformInfo } from '../../models/media.model';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, Button, BadgeModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent {
  platforms = input<PlatformInfo[]>([]);
  historyCount = input<number>(0);
  toggleHistory = output<void>();
}
